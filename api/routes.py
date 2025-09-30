from datetime import datetime
from typing import Any, Callable, Optional
from venv import logger
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from storage.mongo.client import MongoDBClient, get_mongo_client_as_dependency
from storage.redis.service import RedisCache, get_redis_cache
from workflow_builder.automaton.automaton import Automaton
from workflow_builder.state_parser.contract import StateSet
from config import settings

router = APIRouter()


class WorkflowRequest(BaseModel):
    client_session_id: str
    client_workflow_id: Optional[str] = None


class SaveWorkflowRequest(BaseModel):
    states: StateSet
    predefined_context: dict[str, Any] = {}


@router.post("/workflow/save")
async def save_workflow(
    body: SaveWorkflowRequest,
    mongo_client: Callable = Depends(get_mongo_client_as_dependency),
):
    """
    Сохраняет StateModel в MongoDB.
    Args:
        state: Экземпляр StateModel с данными состояния
    Returns:
        dict: Ответ с ID сохраненного документа
    Raises:
        HTTPException: Если сохранение не удалось
    """
    try:
        states_mongo_client: MongoDBClient = mongo_client(collection=settings.STATES_MONGO_COLLECTION)
        workflow_context_client: MongoDBClient = mongo_client(collection=settings.WORKFLOW_MONGO_COLLECTION)
        # Преобразуем Pydantic модель в словарь для сохранения в MongoDB
        state_list = [state.model_dump() for state in body.states.states]
        state_dict = {"states": state_list}
        # Сохраняем документ в MongoDB
        inserted_workflow_id = states_mongo_client.insert_description(state_dict)
        if inserted_workflow_id is None:
            raise HTTPException(status_code=500, detail="Failed to save state to MongoDB")

        wf_context_id = workflow_context_client.insert_description(
            body.predefined_context, overriden_id=inserted_workflow_id
        )
        if wf_context_id is None:
            raise HTTPException(status_code=500, detail="Failed to save workflow context to MongoDB")

        logger.info(f"State successfully saved with ID: {inserted_workflow_id}")
        if inserted_workflow_id:
            return {
                "status": "success",
                "wf_description_id": inserted_workflow_id,
                "wf_context_id": wf_context_id,
            }
        else:
            raise HTTPException(
                status_code=500, detail="Failed to save state to MongoDB"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving state: {str(e)}")


@router.post("/client/workflow")
async def check_session(
    body: WorkflowRequest,
    redis_cache: RedisCache = Depends(get_redis_cache),
):
    """
    Check/create client session and get/initialize workflow state
    """
    session_key = redis_cache.get_session_key(body.client_session_id)
    # Check if session exists
    if redis_cache.r.exists(session_key):
        session_context = redis_cache.get_session(body.client_session_id)
        body.client_workflow_id = session_context.get("__workflow_id")
        logger.info(
            f"Session {body.client_session_id} found; Current workflow: {body.client_workflow_id}"
        )
        # todo: connect the automaton
    else:
        if body.client_workflow_id is None:
            logger.error("Workflow ID is required")
            raise HTTPException(status_code=400, detail="Workflow ID is required")
        session_context = {
            "__workflow_id": body.client_workflow_id,
            "__created_at": str(datetime.now()),
        }
        redis_cache.update_session(body.client_session_id, session_context)
    try:
        automaton = Automaton(session_id=body.client_session_id, workflow_id=body.client_workflow_id)
        automaton.run()
    except Exception as e:
        logger.error(f"Failed to create automaton. Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create automaton. Error: {e}")
    return {
        "session_id": body.client_session_id,
        "context": session_context,
    }
