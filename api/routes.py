from datetime import datetime
from pprint import pprint
from typing import Optional
from venv import logger
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from storage.mongo.client import MongoDBClient, get_mongo_client_as_dependency

from workflow_builder.state_parser.parser import GlobalStateParser
from storage.redis.service import RedisCache, get_redis_cache
from workflow_builder.state_parser.contract import StateModel

router = APIRouter()


class StateSet(BaseModel):
    states: list[StateModel]


class WorkflowRequest(BaseModel):
    client_session_id: str
    client_workflow_id: Optional[str] = None


@router.post("/workflow/save")
async def save_workflow(
    states: StateSet,
    mongo_client: MongoDBClient = Depends(get_mongo_client_as_dependency),
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
        # Преобразуем Pydantic модель в словарь для сохранения в MongoDB
        state_list = [state.model_dump() for state in states.states]
        state_dict = {"states": state_list}
        # Сохраняем документ в MongoDB
        inserted_id = mongo_client.insert_description(state_dict)
        logger.info(f"State successfully saved with ID: {inserted_id}")
        if inserted_id:
            return {"status": "success", "inserted_id": inserted_id}
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
    state_key = f"state:{body.client_session_id}"

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

    # Get or initialize workflow state
    current_state = redis_cache.r.get(state_key)
    if not current_state:
        pass
    return {
        "session_id": body.client_session_id,
        "context": session_context,
        "current_state": current_state,
    }
