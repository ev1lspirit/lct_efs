import json
import uuid
import redis
from config import settings
from utils import GeneralPurposeSingletonMeta, execute_safe


class RedisCache(metaclass=GeneralPurposeSingletonMeta):
    def __init__(self, host: str = settings.REDIS_HOST):
        self.r = redis.Redis(
            host=host,
            port=settings.REDIS_PORT,
            decode_responses=True
        )

    def create_session(self, data: dict) -> str:
        """
        Создает сессию в Redis и возвращает ее идентификатор.

        :param data: словарь с данными сессии
        :return: идентификатор сессии
        """
        session_id = str(uuid.uuid4())
        key = self.get_session_key(session_id)
        self.r.hset(key, mapping=data)  # сохраняем как hash
        return session_id

    def get_session(self, session_id: str) -> dict | None:
        """
        Возвращает сессию по ее идентификатору.

        :param session_id: идентификатор сессии
        :return: словарь с данными сессии или None, если сессия не существует
        """
        raw = self.r.hgetall(self.get_session_key(session_id))
        return {k.decode(): v.decode() for k, v in raw.items()} if raw else None

    def update_session(self, session_id: str, data: dict, ttl: int = 3600):
        key = self.get_session_key(session_id)
        self.r.hset(key, mapping=data)

    def delete_session(self, session_id: str):
        self.r.delete(self.get_session_key(session_id))

    @staticmethod
    def get_screen_key(screen_id: str):
        return f"screen:{screen_id}"

    @staticmethod
    def get_session_key(session_id: str):
        return f"session:{session_id}"

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
        return self.r.scan_iter(f"{index_name}:*")
