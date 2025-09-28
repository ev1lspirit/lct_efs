from storage.redis.service import RedisCache
from utils import GeneralPurposeSingletonMeta


class RedisSessionContext(metaclass=GeneralPurposeSingletonMeta):
    def __init__(self):
        self.redis_cache = RedisCache()

    @property
    def session(self):
        if not hasattr(self, "_session"):
            session_id: bytes = self.redis_cache.r.get("current_session_id") # type: ignore
            if session_id is not None:
                session_id = session_id.decode()
                self._session = self.redis_cache.get_session(session_id))
        return getattr(self, "_session", None)
