from datetime import datetime
from typing import Any, Callable, Optional, Union
from venv import logger
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from storage.mongo.client import MongoDBClient, get_mongo_client_as_dependency
from storage.redis.service import RedisCache, get_redis_cache
from workflow_builder.automaton.automaton import Automaton
from workflow_builder.state_parser.contract import StateSet
from config import settings
from workflow_builder.models import StateTypeEnum

router = APIRouter()


class WorkflowRequest(BaseModel):
    client_session_id: str
    client_workflow_id: Optional[str] = None
    context: dict[str, Union[str, int, list, dict]] = {}
    event_name: Optional[str] = None


class SaveWorkflowRequest(BaseModel):
    states: StateSet
    predefined_context: dict[str, Any] = {}


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


@router.post("/client/workflow")
async def check_session(
    body: WorkflowRequest,
    redis_cache: RedisCache = Depends(get_redis_cache),
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

    try:
        session_context = await _get_or_create_session(body, redis_cache)
        automaton = Automaton(
            session_id=body.client_session_id, workflow_id=body.client_workflow_id
        )
        screen_payload = automaton.run(body.event_name)
        # Получаем обновленный контекст после выполнения workflow
        updated_context = redis_cache.get_session(body.client_session_id)
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
    Save workflow states to MongoDB.

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
        state_dict = {"states": state_list}
        logger.debug(f"Saving {len(state_list)} states to MongoDB")
        # Save to MongoDB
        inserted_id = states_client.insert_description(state_dict)

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
    body: WorkflowRequest, redis_cache: RedisCache
) -> dict[str, Any]:
    """
    Retrieve existing session or create new one with validation

    Args:
        body: WorkflowRequest containing session data
        redis_cache: Redis cache instance

    Returns:
        Session context dictionary

    Raises:
        HTTPException: If workflow ID is missing for new session
    """
    session_key = redis_cache.get_session_key(body.client_session_id)
    if redis_cache.r.exists(session_key):
        return _handle_existing_session(body, redis_cache)
    return _create_new_session(body, redis_cache)


def _handle_existing_session(
    body: WorkflowRequest, redis_cache: RedisCache
) -> dict[str, Any]:
    """Handle existing session retrieval and context updates"""
    logger.info(f"Session found: {body.client_session_id}")

    session_context = redis_cache.get_session(body.client_session_id)
    body.client_workflow_id = session_context.get("__workflow_id")

    logger.info(
        f"Retrieved existing session. Current workflow: {body.client_workflow_id}, "
        f"Event: {body.event_name}"
    )
    # Update session context if new context provided
    if body.context:
        logger.debug(f"Updating session context with: {body.context}")
        session_context.update(body.context)
        redis_cache.update_session(body.client_session_id, session_context)

    return session_context


def _create_new_session(
    body: WorkflowRequest, redis_cache: RedisCache
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

    redis_cache.update_session(body.client_session_id, session_context)

    logger.info(
        f"Created new session: {body.client_session_id} "
        f"with workflow: {body.client_workflow_id}"
    )

    return session_context

