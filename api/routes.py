from datetime import datetime
from typing import Any, Callable
from venv import logger
from fastapi import APIRouter, Depends, HTTPException
from api.schema import SaveWorkflowRequest, WorkflowRequest
from api.utils import _is_valid_session_id
from storage.mongo.client import MongoDBClient, get_mongo_client_as_dependency
from storage.redis.service import AsyncRedisCache, get_redis_cache
from validators.automaton import AutomatonValidator
from workflow_builder.automaton.automaton import Automaton
from config import settings
from workflow_builder.models import StateTypeEnum


router = APIRouter()


@router.post("/workflow/save")
async def save_workflow(
    body: SaveWorkflowRequest,
    mongo_client: Callable = Depends(get_mongo_client_as_dependency),
) -> dict[str, Any]:
    """
    Save StateModel to MongoDB and associated workflow context.

    Args:
        body: SaveWorkflowRequest containing states and predefined context
        mongo_client: MongoDB client dependency

    Returns:
        dict: Response with saved document IDs and status

    Raises:
        HTTPException: If saving to MongoDB fails
    """
    logger.info(
        f"Starting workflow save process. States count: {len(body.states.states)}"
    )
    try:
        breakpoint()
        validator = AutomatonValidator(states=body.states.states)
        validator.run()
        #mongo_client = next(get_mongo_client_as_dependency())
        states_client = mongo_client(collection=settings.STATES_MONGO_COLLECTION)
        workflow_context_client = mongo_client(
            collection=settings.WORKFLOW_MONGO_COLLECTION
        )
        screens_client = mongo_client(collection=settings.SCREENS_MONGO_COLLECTION)
        # Validate input data
        _validate_save_workflow_request(body)
        workflow_id = await _save_workflow_states(body, states_client)
        # Сохраняем экраны после получения workflow_id
        saved_screens = 0
        for state in body.states.states:
            if state.state_type == StateTypeEnum.screen.value and state.screen:
                try:
                    screens_client.upsert_screen(workflow_id, state.name, state.screen)
                    saved_screens += 1
                except Exception as e:
                    logger.error(f"Failed to save screen for state {state.name}: {e}")
        context_id = await _save_workflow_context(
            body, workflow_context_client, workflow_id
        )
        logger.info(
            f"Workflow successfully saved. Workflow ID: {workflow_id}, "
            f"Context ID: {context_id}, Screens saved: {saved_screens}"
        )
        return {
            "status": "success",
            "wf_description_id": workflow_id,
            "wf_context_id": context_id,
            "screens_saved": saved_screens,
        }
    except HTTPException:
        # Re-raise known HTTP exceptions
        logger.warning("Client error during workflow save", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error during workflow save: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Internal server error during workflow save"
        )


@router.get("/workflow/{workflow_id}/full")
async def get_full_workflow(
    workflow_id: str,
    mongo_client: Callable = Depends(get_mongo_client_as_dependency),
) -> dict[str, Any]:
    """
    Get complete workflow including states, screens, and predefined context.

    Args:
        workflow_id: MongoDB document ID of the workflow
        mongo_client: MongoDB client dependency

    Returns:
        dict: Complete workflow data with states, screens, and context

    Raises:
        HTTPException: If workflow not found or retrieval fails
    """
    logger.info(f"Fetching full workflow data for ID: {workflow_id}")

    try:
        states_client = mongo_client(collection=settings.STATES_MONGO_COLLECTION)
        workflow_data = states_client.get_workflow_with_context(workflow_id)

        if not workflow_data:
            logger.warning(f"Workflow {workflow_id} not found")
            raise HTTPException(
                status_code=404, detail=f"Workflow with ID {workflow_id} not found"
            )

        logger.info(f"Successfully retrieved full workflow {workflow_id}")
        return {"status": "success", "workflow_id": workflow_id, "data": workflow_data}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching full workflow {workflow_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Internal server error while fetching workflow"
        )


@router.post("/client/workflow")
async def check_session(
    body: WorkflowRequest,
    redis_cache: AsyncRedisCache = Depends(get_redis_cache),
) -> dict[str, Any]:
    """
    Check/create client session and get/initialize workflow state

    Args:
        body: WorkflowRequest containing session and workflow data
        redis_cache: Redis cache dependency

    Returns:
        Dict with session_id and context

    Raises:
        HTTPException: For client errors (400) or server errors (500)
    """
    logger.info(f"Processing workflow request for session: {body.client_session_id}")

    #redis_cache = await get_redis_cache()
    try:
        await _get_or_create_session(body, redis_cache)
        automaton = Automaton(
            session_id=body.client_session_id, workflow_id=body.client_workflow_id
        )
        screen_payload = await automaton.run(body.event_name)
        # Получаем обновленный контекст после выполнения workflow
        updated_context = await redis_cache.get_session(body.client_session_id)
        logger.info(
            f"Successfully processed workflow for session: {body.client_session_id}"
        )
        response: dict[str, Any] = {
            "session_id": body.client_session_id,
            "context": updated_context,
            "current_state": automaton.current_state.name,
            "state_type": automaton.current_state.type_.value,
        }
        if screen_payload is not None:
            response["screen"] = screen_payload
        return response
    except HTTPException:
        # Re-raise HTTP exceptions to avoid masking client errors
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error processing workflow request: {str(e)}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")


def _validate_save_workflow_request(body: SaveWorkflowRequest) -> None:
    """
    Validate the save workflow request data.

    Args:
        body: SaveWorkflowRequest to validate

    Raises:
        HTTPException: If validation fails
    """
    if not body.states or not body.states.states:
        logger.error("No states provided in save workflow request")
        raise HTTPException(status_code=400, detail="At least one state is required")

    if not body.predefined_context:
        logger.warning("Empty predefined context provided in save workflow request")

    logger.debug(
        f"Validation passed. States: {len(body.states.states)}, "
        f"Context keys: {len(body.predefined_context) if body.predefined_context else 0}"
    )


async def _save_workflow_states(
    body: SaveWorkflowRequest, states_client: MongoDBClient
) -> str:
    """
    Save workflow states to MongoDB with new format validation.

    Args:
        body: SaveWorkflowRequest containing states
        states_client: MongoDB client for states collection

    Returns:
        str: The inserted workflow ID

    Raises:
        HTTPException: If saving states fails
    """
    try:
        # Convert Pydantic models to dictionaries
        state_list = [state.model_dump() for state in body.states.states]
        workflow_data = {
            "states": state_list,
            "predefined_context": body.predefined_context,
        }
        logger.debug(
            f"Saving {len(state_list)} states to MongoDB with new format validation"
        )

        # Save to MongoDB using new method with format validation
        inserted_id = states_client.insert_workflow_with_format_validation(
            workflow_data
        )

        if not inserted_id:
            logger.error("MongoDB returned no ID for inserted states document")
            raise HTTPException(
                status_code=500, detail="Failed to save workflow states to database"
            )

        logger.info(f"Workflow states saved successfully with ID: {inserted_id}")
        return inserted_id

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save workflow states: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Database error while saving workflow states: {str(e)}",
        )


async def _save_workflow_context(
    body: SaveWorkflowRequest, context_client: MongoDBClient, workflow_id: str
) -> str:
    """
    Save workflow context to MongoDB using the provided workflow ID.

    Args:
        body: SaveWorkflowRequest containing predefined context
        context_client: MongoDB client for workflow context collection
        workflow_id: The workflow ID to use for context document

    Returns:
        str: The inserted context ID (should match workflow_id)

    Raises:
        HTTPException: If saving context fails
    """
    try:
        logger.debug(f"Saving workflow context with ID: {workflow_id}")

        context_id = context_client.insert_description(
            body.predefined_context, overriden_id=workflow_id
        )

        if not context_id:
            logger.error("MongoDB returned no ID for inserted context document")
            raise HTTPException(
                status_code=500, detail="Failed to save workflow context to database"
            )

        if context_id != workflow_id:
            logger.warning(
                f"Context ID {context_id} does not match workflow ID {workflow_id}. "
                "This may indicate an issue with the overriden_id parameter."
            )

        logger.info(f"Workflow context saved successfully with ID: {context_id}")
        return context_id

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save workflow context: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Database error while saving workflow context: {str(e)}",
        )


async def _get_or_create_session(
    body: WorkflowRequest, redis_cache: AsyncRedisCache
) -> dict[str, Any]:
    """
    Retrieve existing session or create new one with validation

    Args:
        body: WorkflowRequest containing session data
        redis_cache: Redis cache instance

    Returns:
        Session context dictionary

    Raises:
        HTTPException: If workflow ID is missing for new session or validation fails
    """
    # Валидация session_id формата (должен быть UUID или безопасная строка)
    if not _is_valid_session_id(body.client_session_id):
        logger.error(f"Invalid session_id format: {body.client_session_id}")
        raise HTTPException(
            status_code=400,
            detail="Invalid session_id format. Expected UUID or alphanumeric string",
        )

    # Атомарно получаем сессию (get_session теперь возвращает None если не существует)
    session_context = await redis_cache.get_session(body.client_session_id)

    if session_context is not None:
        return await _handle_existing_session(body, redis_cache, session_context)
    return await _create_new_session(body, redis_cache)


async def _handle_existing_session(
    body: WorkflowRequest, redis_cache: AsyncRedisCache, session_context: dict
) -> dict[str, Any]:
    """Handle existing session retrieval and context updates"""
    logger.info(f"Session found: {body.client_session_id}")
    stored_workflow_id = session_context.get("__workflow_id")

    # Проверка на отсутствие workflow_id в сессии (критическая ошибка)
    if not stored_workflow_id:
        logger.error(
            f"Session {body.client_session_id} exists but has no workflow_id. "
            "This indicates corrupted session data."
        )
        raise HTTPException(
            status_code=500, detail="Session data corrupted: missing workflow_id"
        )

    # Проверка на попытку сменить workflow_id
    if body.client_workflow_id and body.client_workflow_id != stored_workflow_id:
        logger.warning(
            f"Attempt to change workflow_id for session {body.client_session_id}: "
            f"{stored_workflow_id} -> {body.client_workflow_id}. Ignoring new workflow_id."
        )
        # Можно либо игнорировать, либо вернуть ошибку. Выберем игнорирование с предупреждением.

    # Используем сохраненный workflow_id
    body.client_workflow_id = stored_workflow_id

    logger.info(
        f"Retrieved existing session. Current workflow: {body.client_workflow_id}, "
        f"Event: {body.event_name}"
    )

    # Update session context if new context provided
    if body.context:
        logger.debug(f"Updating session context with: {body.context}")
        session_context.update(body.context)
        await redis_cache.update_session(body.client_session_id, session_context)

    return session_context


async def _create_new_session(
    body: WorkflowRequest, redis_cache: AsyncRedisCache
) -> dict[str, Any]:
    """Create new session with validation"""
    if body.client_workflow_id is None:
        logger.error("Workflow ID required for new session")
        raise HTTPException(
            status_code=400, detail="Workflow ID is required for new session"
        )

    session_context = {
        "__workflow_id": body.client_workflow_id,
        "__created_at": str(datetime.now()),
    }

    # Add initial context if provided
    if body.context:
        session_context.update(body.context)

    # Создаем сессию с TTL (по умолчанию 3600 секунд = 1 час)
    await redis_cache.update_session(body.client_session_id, session_context, ttl=3600)

    logger.info(
        f"Created new session: {body.client_session_id} "
        f"with workflow: {body.client_workflow_id}"
    )

    return session_context
