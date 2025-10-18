import json
import logging
from typing import Any
import uuid
import redis.asyncio as redis
from attrs import define, field
from config import settings
from utils import (
    GeneralPurposeSingletonMeta,
    dump_context,
    execute_safe,
    prepare_context_response,
)


logger = logging.getLogger(__name__)


class DefinedKeysMixin:

    def workflow_context_key(self, session_id: str):
        return f"workflow_context:{session_id}"

    def screen_key(self, screen_id: str):
        return f"screen:{screen_id}"

    def session_key(self, session_id: str):
        return f"session:{session_id}"

    def session_state_key(self, session_id: str):
        return f"state:{session_id}"


@define
class AsyncRedisCache(DefinedKeysMixin, metaclass=GeneralPurposeSingletonMeta):
    redis: Any = field(init=False)

    def __attrs_post_init__(self):
        self.redis = redis.from_url(settings.redis_url)

    @execute_safe(default_return=None, service_name="Redis")
    async def save_state(self, session_id: str, state_obj: dict):
        redis_key = self.session_state_key(session_id)
        await self.redis.hset(redis_key, mapping=state_obj)

    @execute_safe(default_return=None, service_name="Redis")
    async def set_workflow_context(self, session_id: str, context: dict):
        redis_key = self.workflow_context_key(session_id)
        await self.redis.hset(redis_key, mapping=dump_context(context))

    @execute_safe(default_return=None, service_name="Redis")
    async def get_workflow_context(self, session_id: str):
        redis_key = f"workflow_context:{session_id}"
        try:
            value = await self.redis.hgetall(name=redis_key)
            return prepare_context_response(value)
        except Exception as exc:
            logger.error("Error: ")
            raise exc

    @execute_safe(default_return=None, service_name="Redis")
    async def get_state(self, session_id: str):
        redis_key = f"state:{session_id}"
        state = await self.redis.hgetall(redis_key)
        return prepare_context_response(state)

    @execute_safe(default_return=None, service_name="Redis")
    async def create_session(self, data: dict, ttl: int = 3600) -> str:
        """
        Создает сессию в Redis и возвращает ее идентификатор.

        :param data: словарь с данными сессии
        :param ttl: время жизни сессии в секундах (по умолчанию 3600)
        :return: идентификатор сессии
        """
        session_id = str(uuid.uuid4())
        key = self.session_key(session_id)
        await self.redis.hset(key, mapping=data)  # сохраняем как hash
        await self.redis.expire(key, ttl)  # Устанавливаем TTL
        logger.debug(f"Created session {session_id} with TTL {ttl}s")
        return session_id

    @execute_safe(default_return=None, service_name="Redis")
    async def get_session(self, session_id: str) -> dict | None:
        """
        Возвращает сессию по ее идентификатору.

        :param session_id: идентификатор сессии
        :return: словарь с данными сессии или None, если сессия не существует
        """
        key = self.session_key(session_id)
        # Проверяем существование ключа перед получением
        if not await self.redis.exists(key):
            return None

        raw = await self.redis.hgetall(key)
        result = prepare_context_response(raw)

        # Дополнительная проверка: если ключ существует, но пустой
        if not result:
            logger.warning(f"Session key {key} exists but is empty")
            return None

        return result

    @execute_safe(default_return=None, service_name="Redis")
    async def update_session(self, session_id: str, data: dict, ttl: int = 3600):
        """
        Обновляет сессию и продлевает TTL

        :param session_id: идентификатор сессии
        :param data: данные для обновления
        :param ttl: время жизни сессии в секундах (по умолчанию 3600)
        """
        key = self.session_key(session_id)
        if data:
            await self.redis.hset(key, mapping=dump_context(data))
            # Обновляем TTL при каждом обновлении сессии
            await self.redis.expire(key, ttl)
            logger.debug(f"Session {session_id} updated with TTL {ttl}s")

    async def delete_session(self, session_id: str):
        await self.redis.delete(self.session_key(session_id))

    @execute_safe(default_return=False, service_name="Redis")
    async def check_screen(self, screen_id: str):
        return await self.redis.exists(screen_id)

    @execute_safe(default_return=None, service_name="Redis")
    async def cache_screen(self, screen_id: str, screen: dict):
        await self.redis.set(self.screen_key(screen_id), json.dumps(screen), 1)

    @execute_safe(default_return=0, service_name="Redis")
    async def cache_many(self, screen_mapping: dict[str, dict]) -> int:
        # to self
        pipe = await self.redis.pipeline()

        for key, value in screen_mapping.items():
            await pipe.set(self.screen_key(key), json.dumps(value), nx=True)

        results = await pipe.execute()
        added_amount: int = sum(filter(None, results))
        return added_amount

    @execute_safe(default_return=None, service_name="Redis")
    async def delete_key(self, screen_id: str):
        await self.redis.delete(self.screen_key(screen_id))

    @execute_safe(default_return=None, service_name="Redis")
    async def get_all_screens(self, index_name: str = "screen"):
        results = []
        async for result in self.redis.scan_iter(f"{index_name}:*"):
            results.append(prepare_context_response(result))
        return results


async def get_redis_cache() -> AsyncRedisCache:
    return AsyncRedisCache()


async def main():
    cache = await get_redis_cache()
    session = await cache.create_session({"k": "001"})
    print(session)
    await cache.delete_session(session)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
