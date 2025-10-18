import json
import logging
from storage.redis.service import AsyncRedisCache
from workflow_builder.automaton.models import StateMetadata
from workflow_builder.models import StateTypeEnum
from config import settings


logger = logging.getLogger(__name__)


class SessionContext:
    _redis_cache: AsyncRedisCache = AsyncRedisCache()

    def __init__(self, session_id, workflow_id: str):
        self._session_id = session_id
        self._workflow_id = workflow_id

    @property
    def session(self):
        if not hasattr(self, "_session"):
            self._session = self._get_session_context()
        return getattr(self, "_session", {})

    async def _get_session_context(self):
        try:
            session = await self._redis_cache.get_session(self._session_id)

            # Проверяем, что сессия действительно существует
            if session is None:
                logger.error(
                    f"Session {self._session_id} not found in Redis. "
                    "It may have expired or never been created."
                )
                raise ValueError(f"Session {self._session_id} not found")

            # Проверяем наличие обязательного поля __workflow_id
            if "__workflow_id" not in session:
                logger.error(
                    f"Session {self._session_id} is missing __workflow_id. "
                    "Session data may be corrupted."
                )
                raise ValueError(f"Session {self._session_id} has corrupted data")

            return session
        except Exception as e:
            logger.error(f"Failed to get session. Error: {e}")
            raise e

    def get(self, key):
        return self.session.get(key)

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc_value, traceback):
        try:
            await self.update_session()
        except Exception as e:
            logger.error(f"Failed to update session. Error: {e}")
            raise e

    async def update_session_state(self, data: StateMetadata):
        logger.info(f"Updating session state: {self._session_id} with data: ")
        try:
            await self._redis_cache.save_state(self._session_id, data.model_dump())
        except Exception as e:
            logger.error(f"Failed to update session state. Error: {e}")
            raise e

    async def get_session_state(self):
        state_meta = await self._redis_cache.get_state(self._session_id)
        return StateMetadata(
            name=state_meta.get("name", settings.SERVICE_INIT_STATE),
            type_=StateTypeEnum(state_meta.get("type", "service")),
        )

    async def update_session(self):
        if hasattr(self, "_session") and self._session is not None:
            logger.info(
                f"Updating session: {self._session_id} with data: {json.dumps(self._session)}"
            )
            flat_context = {
                k: json.dumps(v) if isinstance(v, (dict, list)) else v
                for k, v in self.session.items()
            }
            await self._redis_cache.update_session(self._session_id, flat_context)
