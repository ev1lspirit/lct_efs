from datetime import datetime
from venv import logger
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Optional
from storage.mongo.client import MongoDBClient, get_mongo_client

from storage.redis.service import RedisCache, get_redis_cache
from workflow_builder.state_parser.contract import StateModel
from workflow_builder.state_parser.parser import GlobalStateParser
from workflow_builder.automaton.automaton import Automaton
from context import save_user_input, get_context

router = APIRouter()


class UserEventRequest(BaseModel):
    """Модель для пользовательского события от фронта ЕФС"""
    event_name: str
    event_data: Optional[Any] = None
    result_variable: Optional[str] = None


class ScreenRequest(BaseModel):
    """Модель для запроса экрана"""
    workflow_id: str
    current_state: str
    session_id: str


@router.post("/workflow/save")
async def save_workflow(states: list[StateModel], mongo_client: MongoDBClient = Depends(get_mongo_client)):
    """Сохраняет StateModel в MongoDB"""
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


@router.post("/efs/user-event")
async def handle_user_event(
    event_request: UserEventRequest,
    redis_cache: RedisCache = Depends(get_redis_cache),
):
    """
    Обрабатывает пользовательское событие от фронта ЕФС
    """
    try:
        # Сохраняем пользовательский ввод в контекст
        if event_request.event_data is not None:
            success = save_user_input(
                event_request.event_name,
                event_request.event_data,
                event_request.result_variable
            )
            if not success:
                logger.warning(f"Failed to save user input for event: {event_request.event_name}")

        # Получаем текущий workflow и состояние из сессии
        session_id = redis_cache.r.get("current_session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="No active session found")

        session_id = session_id.decode()
        session_data = redis_cache.get_session(session_id)

        if not session_data or "workflow_id" not in session_data or "current_state" not in session_data:
            raise HTTPException(status_code=400, detail="Session does not contain workflow information")

        workflow_id = session_data["workflow_id"]
        current_state_name = session_data["current_state"]

        # Создаем парсер и автомат
        parser = GlobalStateParser(current_state_name, workflow_id)
        states = list(parser.parse_states())
        automaton = Automaton(states)

        # Выполняем следующий шаг автомата с пользовательским событием
        try:
            automaton.run(event_name=event_request.event_name)

            # Обновляем текущее состояние в сессии
            session_data["current_state"] = automaton.current_state.name
            redis_cache.set_session(session_id, session_data)

            # Если новое состояние - экран, возвращаем его данные
            if automaton.current_state.type_.value == "screen":
                screen_data = automaton.current_state.send_to_front()
                return {
                    "status": "success",
                    "next_screen": screen_data,
                    "current_state": automaton.current_state.name
                }
            else:
                return {
                    "status": "processing",
                    "current_state": automaton.current_state.name,
                    "message": "Processing technical or integration state"
                }

        except ValueError as e:
            # Если нет подходящего перехода, возвращаем текущий экран
            return {
                "status": "no_transition",
                "message": str(e),
                "current_state": current_state_name
            }

    except Exception as e:
        logger.error(f"Error handling user event: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing user event: {str(e)}")


@router.get("/efs/screen/{screen_name}")
async def get_screen(screen_name: str):
    """
    Получает экран по имени из MongoDB с подстановкой контекстных переменных
    """
    try:
        from workflow_builder.states import ScreenState
        from workflow_builder.transitions import Transition

        # Создаем временный экземпляр ScreenState для получения экрана
        screen_state = ScreenState(
            name=screen_name,
            final=False,
            transitions=[],
            expressions=[]
        )

        screen_data = screen_state.send_to_front()

        return {
            "status": "success",
            "screen_data": screen_data
        }

    except Exception as e:
        logger.error(f"Error getting screen '{screen_name}': {e}")
        raise HTTPException(status_code=404, detail=f"Screen '{screen_name}' not found or error loading: {str(e)}")


@router.get("/client/workflow")
async def check_session(
    client_session_id: str,
    client_workflow_id: str,
    redis_cache: RedisCache = Depends(get_redis_cache),
):
    """
    Check/create client session and get/initialize workflow state
    """
    try:
        # Устанавливаем текущую сессию
        redis_cache.r.set("current_session_id", client_session_id)

        # Получаем или создаем сессию
        session_data = redis_cache.get_session(client_session_id)
        if not session_data:
            session_data = {
                "workflow_id": client_workflow_id,
                "current_state": "initial",  # Будет обновлено после инициализации
                "created_at": datetime.now().isoformat()
            }
            redis_cache.set_session(client_session_id, session_data)

        # Инициализируем workflow если необходимо
        parser = GlobalStateParser("initial", client_workflow_id)
        states = list(parser.parse_states())
        automaton = Automaton(states)

        # Находим начальное состояние
        initial_state = automaton.current_state
        session_data["current_state"] = initial_state.name
        redis_cache.set_session(client_session_id, session_data)

        # Если начальное состояние - экран, возвращаем его
        if initial_state.type_.value == "screen":
            screen_data = initial_state.send_to_front()
            return {
                "status": "success",
                "initial_screen": screen_data,
                "current_state": initial_state.name
            }
        else:
            # Если техническое состояние, выполняем автомат до первого экрана
            try:
                automaton.run()
                session_data["current_state"] = automaton.current_state.name
                redis_cache.set_session(client_session_id, session_data)

                if automaton.current_state.type_.value == "screen":
                    screen_data = automaton.current_state.send_to_front()
                    return {
                        "status": "success",
                        "initial_screen": screen_data,
                        "current_state": automaton.current_state.name
                    }
            except Exception as e:
                logger.error(f"Error running automaton: {e}")

        return {
            "status": "success",
            "current_state": automaton.current_state.name,
            "message": "Workflow initialized"
        }

    except Exception as e:
        logger.error(f"Error in check_session: {e}")
        raise HTTPException(status_code=500, detail=f"Error initializing session: {str(e)}")
