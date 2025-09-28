from datetime import datetime
from venv import logger
from fastapi import APIRouter, Depends, HTTPException
from storage.mongo.client import MongoDBClient, get_mongo_client

from storage.redis.service import RedisCache, get_redis_cache
from workflow_builder.state_parser.contract import StateModel

router = APIRouter()


@router.post("/workflow/save")
async def save_workflow(states: list[StateModel], mongo_client: MongoDBClient = Depends(get_mongo_client)):
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
        state_list = [state.model_dump() for state in states]
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


from workflow_builder.state_parser.parser import GlobalStateParser


@router.get("/client/workflow")
async def check_session(
    client_session_id: str,
    client_workflow_id: str,
    redis_cache: RedisCache = Depends(get_redis_cache),
):
    """
    Check/create client session and get/initialize workflow state
    """
    session_key = redis_cache.get_session_key(client_session_id)
    state_key = f"state:{client_session_id}"

    # Check if session exists
    if redis_cache.r.exists(session_key):
        session_context = redis_cache.r.hgetall(session_key)
    else:
        # Create new session
        session_context = {
            "workflow_id": client_workflow_id,
            "created_at": str(datetime.now()),
        }
        redis_cache.update_session(client_session_id, session_context)

    # Get or initialize workflow state
    current_state = redis_cache.r.get(state_key)
    if not current_state:
        # Initialize workflow parser to get initial state
        parser = GlobalStateParser(current_state_name="Init", workflow_id=client_workflow_id)
        workflow_states = parser.parse_states()

        # Find initial state
        initial_state = next(
            (state.name for state in workflow_states if state.initial_state), None
        )

        if not initial_state:
            raise HTTPException(
                status_code=400, detail="Workflow has no initial state defined"
            )

        # Save initial state
        redis_cache.r.set(state_key, initial_state)
        current_state = initial_state

    return {
        "session_id": client_session_id,
        "context": session_context,
        "current_state": current_state,
    }
