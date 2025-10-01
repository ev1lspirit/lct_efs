from datetime import datetime
import os
import timeit
import logging
import traceback
from typing import Any, Callable, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.exceptions import RequestValidationError
import psutil
from pydantic import BaseModel, ValidationError
from storage.mongo.client import MongoDBClient, get_mongo_client_as_dependency
from storage.redis.service import RedisCache, get_redis_cache
from workflow_builder.automaton.automaton import Automaton
from workflow_builder.state_parser.contract import StateSet
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class WorkflowRequest(BaseModel):
    client_session_id: str
    client_workflow_id: Optional[str] = None
    # context: dict[str, Any] = {}
    event_name: Optional[str] = None


class SaveWorkflowRequest(BaseModel):
    states: StateSet
    predefined_context: dict[str, Any] = {}


@router.post("/workflow/save")
async def save_workflow(
    request: Request,
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
    # Логируем входящие данные для отладки
    try:
        raw_body = await request.body()
        logger.info(f"📥 Received POST /workflow/save from {request.client.host}")
        logger.debug(f"📋 Raw request body: {raw_body.decode('utf-8')[:1000]}...")  # Первые 1000 символов
        logger.info(f"✅ Body parsed successfully. States count: {len(body.states.states)}")
        
        # Детальная информация о каждом state
        for i, state in enumerate(body.states.states):
            logger.debug(f"  State {i}: type={state.state_type}, name={state.name}, "
                        f"initial={state.initial_state}, final={state.final_state}")
    except Exception as e:
        logger.error(f"❌ Failed to log request body: {e}")
    
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
            logger.info(f"✅ Workflow saved successfully! ID: {inserted_workflow_id}")
            return {
                "status": "success",
                "wf_description_id": inserted_workflow_id,
                "wf_context_id": wf_context_id,
            }
        else:
            raise HTTPException(
                status_code=500, detail="Failed to save state to MongoDB"
            )
    except ValidationError as ve:
        logger.error(f"❌ Validation Error in save_workflow:")
        for error in ve.errors():
            logger.error(f"  - Field: {error['loc']}, Error: {error['msg']}, Value: {error.get('input', 'N/A')}")
        raise HTTPException(status_code=422, detail=ve.errors())
    except Exception as e:
        logger.error(f"❌ Unexpected error in save_workflow: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error saving state: {str(e)}")


@router.post("/client/workflow")
async def check_session(
    body: WorkflowRequest,
    redis_cache: RedisCache = Depends(get_redis_cache),
):
    """
    Check/create client session and get/initialize workflow state
    """
    logger.info(f"📥 Received POST /client/workflow")
    logger.debug(f"📋 Request body: session_id={body.client_session_id}, workflow_id={body.client_workflow_id}, event_name={body.event_name}")
    
    session_key = redis_cache.get_session_key(body.client_session_id)
    logger.debug(f"🔑 Session key: {session_key}")
    
    # Check if session exists
    if redis_cache.r.exists(session_key):
        logger.info(f"✅ Session {body.client_session_id} exists in Redis")
        session_context = redis_cache.get_session(body.client_session_id)
        
        # Используем workflow_id из запроса, если он указан, иначе из сессии
        if body.client_workflow_id is None:
            body.client_workflow_id = session_context.get("__workflow_id")
            logger.info(f"📂 Using workflow_id from session: {body.client_workflow_id}")
        else:
            logger.info(f"📂 Using workflow_id from request: {body.client_workflow_id}")
            # Обновляем workflow_id в сессии, если он изменился
            if body.client_workflow_id != session_context.get("__workflow_id"):
                logger.warning(f"⚠️  Workflow ID changed: {session_context.get('__workflow_id')} → {body.client_workflow_id}")
                session_context["__workflow_id"] = body.client_workflow_id
                redis_cache.update_session(body.client_session_id, session_context)
        
        logger.debug(f"📦 Session context: {session_context}")
        # todo: connect the automaton
    else:
        logger.info(f"🆕 Session {body.client_session_id} does NOT exist, creating new")
        if body.client_workflow_id is None:
            logger.error("❌ Workflow ID is required for new session")
            raise HTTPException(status_code=400, detail="Workflow ID is required")
        session_context = {
            "__workflow_id": body.client_workflow_id,
            "__created_at": str(datetime.now()),
        }
        logger.info(f"💾 Creating new session with workflow_id: {body.client_workflow_id}")
        redis_cache.update_session(body.client_session_id, session_context)
        logger.debug(f"✅ Session saved to Redis: {session_context}")
    
    try:
        logger.info(f"🤖 Initializing Automaton for session={body.client_session_id}, workflow={body.client_workflow_id}")
        automaton  = Automaton(
            session_id=body.client_session_id, workflow_id=body.client_workflow_id
        )
        logger.info(f"▶️  Running automaton with event_name={body.event_name}")
        automaton.run(body.event_name)
        logger.info(f"✅ Automaton execution completed successfully")
    except ValueError as ve:
        # Специфичная обработка для "Workflow not found"
        if "Workflow" in str(ve) and "not found" in str(ve):
            logger.error(f"❌ Workflow {body.client_workflow_id} does not exist in MongoDB")
            logger.error(f"💡 Hint: Make sure you've saved the workflow using POST /workflow/save first")
            raise HTTPException(
                status_code=404, 
                detail=f"Workflow '{body.client_workflow_id}' not found. Please save the workflow first using /workflow/save endpoint."
            )
        else:
            logger.error(f"❌ ValueError in automaton: {str(ve)}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"❌ Failed to create/run automaton. Error: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to create automaton. Error: {e}")
    
    logger.info(f"🎉 Request completed successfully for session {body.client_session_id}")
    return {
        "session_id": body.client_session_id,
        "context": session_context,
    }


@router.get("/workflow/{workflow_id}/exists")
async def check_workflow_exists(
    workflow_id: str,
    mongo_client: Callable = Depends(get_mongo_client_as_dependency),
):
    """
    Check if workflow exists in MongoDB
    """
    logger.info(f"📥 Checking if workflow {workflow_id} exists")
    try:
        states_mongo_client: MongoDBClient = mongo_client(collection=settings.STATES_MONGO_COLLECTION)
        workflow = states_mongo_client.get_description(workflow_id)
        
        if workflow:
            logger.info(f"✅ Workflow {workflow_id} found")
            return {
                "exists": True,
                "workflow_id": workflow_id,
                "states_count": len(workflow.get("states", []))
            }
        else:
            logger.info(f"❌ Workflow {workflow_id} not found")
            return {
                "exists": False,
                "workflow_id": workflow_id
            }
    except Exception as e:
        logger.error(f"❌ Error checking workflow: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error checking workflow: {str(e)}")
