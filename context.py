import json
import logging
from storage.redis.service import RedisCache


logger = logging.getLogger(__name__)

class SessionContext:
    _redis_cache: RedisCache = RedisCache()

    def __init__(self, session_id):
        self.__session_id = session_id

    @property
    def session(self):
        if not hasattr(self, "_session"):
            self._session = self._redis_cache.get_session(self.__session_id)
        return getattr(self, "_session", {})

    def update_session(self):
        if hasattr(self, "_session") and self._session is not None:
            logger.info("Updating session: %s with data: %s", self.__session_id, json.dumps(self._session))
            self._redis_cache.update_session(self.__session_id, self._session)
