from storage.redis.service import RedisCache
from utils import GeneralPurposeSingletonMeta
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class RedisSessionContext(metaclass=GeneralPurposeSingletonMeta):
    def __init__(self):
        self.redis_cache = RedisCache()

    @property
    def session(self):
        if not hasattr(self, "_session"):
            session_id: bytes = self.redis_cache.r.get("current_session_id")  # type: ignore
            if session_id is not None:
                session_id = session_id.decode()
                self._session = self.redis_cache.get_session(session_id)  # Убираем лишнюю скобку
        return getattr(self, "_session", None)

    def get_context_variable(self, variable_name: str) -> Any:
        """Получает значение контекстной переменной"""
        try:
            if self.session:
                return self.session.get(variable_name)
            else:
                logger.warning("No active session found")
                return None
        except Exception as e:
            logger.error(f"Error getting context variable '{variable_name}': {e}")
            return None

    def set_context_variable(self, variable_name: str, value: Any) -> bool:
        """Устанавливает значение контекстной переменной"""
        try:
            if self.session:
                self.session[variable_name] = value
                # Сохраняем обновленную сессию в Redis
                session_id = self.redis_cache.r.get("current_session_id")
                if session_id:
                    session_id = session_id.decode()
                    self.redis_cache.set_session(session_id, self.session)
                    logger.info(f"Context variable '{variable_name}' set to: {value}")
                    return True
            logger.warning("No active session found")
            return False
        except Exception as e:
            logger.error(f"Error setting context variable '{variable_name}': {e}")
            return False

    def save_user_input(self, event_name: str, value: Any, result_variable: str = None) -> bool:
        """Сохраняет результат пользовательского ввода в контекст"""
        try:
            # Если указана переменная результата, используем её
            if result_variable:
                variable_name = result_variable
            else:
                # Иначе создаем имя на основе события
                variable_name = f"{event_name}_result"

            return self.set_context_variable(variable_name, value)
        except Exception as e:
            logger.error(f"Error saving user input for event '{event_name}': {e}")
            return False


# Глобальная функция для получения контекста
def get_context(variable_name: str) -> Any:
    """Глобальная функция для получения контекстной переменной"""
    context = RedisSessionContext()
    return context.get_context_variable(variable_name)


# Глобальная функция для установки контекста
def set_context(variable_name: str, value: Any) -> bool:
    """Глобальная функция для установки контекстной переменной"""
    context = RedisSessionContext()
    return context.set_context_variable(variable_name, value)


# Функция для сохранения пользовательского ввода
def save_user_input(event_name: str, value: Any, result_variable: str = None) -> bool:
    """Глобальная функция для сохранения пользовательского ввода"""
    context = RedisSessionContext()
    return context.save_user_input(event_name, value, result_variable)
