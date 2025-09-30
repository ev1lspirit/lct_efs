import json
import logging
from storage.redis.service import RedisCache
from workflow_builder.automaton.models import StateMetadata
from workflow_builder.models import StateTypeEnum
from config import settings


logger = logging.getLogger(__name__)

class SessionContext:
    _redis_cache: RedisCache = RedisCache()

    def __init__(self, session_id, workflow_id: str):
        self._session_id = session_id
        self._workflow_id = workflow_id

    @property
    def session(self):
        if not hasattr(self, "_session"):
            self._session = self._get_session_context()
        return getattr(self, "_session", {})

    def _get_session_context(self):
        try:
            return self._redis_cache.get_session(self._session_id)
        except Exception as e:
            logger.error(f"Failed to get session. Error: {e}")
            raise e

    def get(self, key):
        return self.session.get(key)

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self.update_session()
        except Exception as e:
            logger.error(f"Failed to update session. Error: {e}")
            raise e

    def update_session_state(self, data: StateMetadata):
        logger.info("Updating session state: %s with data: %s", self._session_id)
        try:
            self._redis_cache.save_state(self._session_id, data.model_dump())
        except Exception as e:
            logger.error(f"Failed to update session state. Error: {e}")
            raise e

    def get_session_state(self):
        state_meta = self._redis_cache.get_state(self._session_id)
        return StateMetadata(
            name=state_meta.get("name", settings.SERVICE_INIT_STATE),
            type_=StateTypeEnum(state_meta.get("type", "service")),
        )

    def update_session(self):
        if hasattr(self, "_session") and self._session is not None:
            logger.info("Updating session: %s with data: %s", self._session_id, json.dumps(self._session))
            flat_context = {
                k: json.dumps(v) if isinstance(v, (dict, list)) else v
                for k, v in self.session.items()
            }
            self._redis_cache.update_session(self._session_id, flat_context)
