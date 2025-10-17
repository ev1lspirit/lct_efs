import json
import logging
import uuid
import redis
from config import settings
from utils import GeneralPurposeSingletonMeta, dump_context, execute_safe, prepare_context_response


logger = logging.getLogger(__name__)

class RedisCache(metaclass=GeneralPurposeSingletonMeta):
    def __init__(self):
        self.r = redis.Redis.from_url(settings.redis_url)

    def save_state(self, session_id: str, state_obj: dict):
        redis_key = self.get_session_state_key(session_id)
        self.r.hset(redis_key, mapping=state_obj)

    def get_wf_context_key(self, session_id: str):
        return f"workflow_context:{session_id}"

    def set_workflow_context(self, session_id: str, context: dict):
        redis_key = self.get_wf_context_key(session_id)

        try:
            self.r.hset(redis_key, mapping=dump_context(context))
        except Exception as exc:
            logger.error("Error: ")
            raise exc

    def get_workflow_context(self, session_id: str):
        redis_key = f"workflow_context:{session_id}"
        try:
            value = self.r.hgetall(name=redis_key)
            return prepare_context_response(value)
        except Exception as exc:
            logger.error("Error: ")
            raise exc

    def get_state(self, session_id: str):
        redis_key = f"state:{session_id}"
        state = self.r.hgetall(redis_key)
        return prepare_context_response(state)

    def create_session(self, data: dict, ttl: int = 3600) -> str:
        """
        Создает сессию в Redis и возвращает ее идентификатор.

        :param data: словарь с данными сессии
        :param ttl: время жизни сессии в секундах (по умолчанию 3600)
        :return: идентификатор сессии
        """
        session_id = str(uuid.uuid4())
        key = self.get_session_key(session_id)
        self.r.hset(key, mapping=data)  # сохраняем как hash
        self.r.expire(key, ttl)  # Устанавливаем TTL
        logger.debug(f"Created session {session_id} with TTL {ttl}s")
        return session_id

    def get_session(self, session_id: str) -> dict | None:
        """
        Возвращает сессию по ее идентификатору.

        :param session_id: идентификатор сессии
        :return: словарь с данными сессии или None, если сессия не существует
        """
        key = self.get_session_key(session_id)
        # Проверяем существование ключа перед получением
        if not self.r.exists(key):
            return None
        
        raw = self.r.hgetall(key)
        result = prepare_context_response(raw)
        
        # Дополнительная проверка: если ключ существует, но пустой
        if not result:
            logger.warning(f"Session key {key} exists but is empty")
            return None
            
        return result

    def update_session(self, session_id: str, data: dict, ttl: int = 3600):
        """
        Обновляет сессию и продлевает TTL
        
        :param session_id: идентификатор сессии
        :param data: данные для обновления
        :param ttl: время жизни сессии в секундах (по умолчанию 3600)
        """
        key = self.get_session_key(session_id)
        if data:
            self.r.hset(key, mapping=dump_context(data))
            # Обновляем TTL при каждом обновлении сессии
            self.r.expire(key, ttl)
            logger.debug(f"Session {session_id} updated with TTL {ttl}s")

    def delete_session(self, session_id: str):
        self.r.delete(self.get_session_key(session_id))

    @staticmethod
    def get_screen_key(screen_id: str):
        return f"screen:{screen_id}"

    @staticmethod
    def get_session_key(session_id: str):
        return f"session:{session_id}"

    @staticmethod
    def get_session_state_key(session_id: str):
        return f"state:{session_id}"

    @execute_safe(default_return=False, service_name="Redis")
    def check_screen(self, screen_id: str):
        return self.r.exists(screen_id)

    @execute_safe(default_return=None, service_name="Redis")
    def cache_screen(self, screen_id: str, screen: dict):
        self.r.set(self.get_screen_key(screen_id), json.dumps(screen), 1)

    @execute_safe(default_return=0, service_name="Redis")
    def cache_many(self, screen_mapping: dict[str, dict]) -> int:
        # to self
        pipe = self.r.pipeline()

        for key, value in screen_mapping.items():
            pipe.set(self.get_screen_key(key), json.dumps(value), nx=True)

        results = pipe.execute()
        added_amount: int = sum(filter(None, results))
        return added_amount

    @execute_safe(default_return=None, service_name="Redis")
    def delete_key(self, screen_id: str):
        self.r.delete(self.get_screen_key(screen_id))

    @execute_safe(default_return=None, service_name="Redis")
    def get_all_screens(self, index_name: str = "screen"):
        results = []
        for result in self.r.scan_iter(f"{index_name}:*"):
            results.append(prepare_context_response(result))
        return results


def get_redis_cache():
    return RedisCache()
