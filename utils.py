from functools import wraps
from typing import Any, Optional, Type
import logging


def setup_logging():

    class ColorFormatter(logging.Formatter):
        COLORS = {
            logging.DEBUG: "\033[37m",  # gray
            logging.INFO: "\033[32m",  # green
            logging.WARNING: "\033[33m",  # yellow
            logging.ERROR: "\033[31m",  # red
            logging.CRITICAL: "\033[41m",  # red background
        }

        def format(self, record):
            color = self.COLORS.get(record.levelno, "\033[0m")
            message = super().format(record)
            return f"{color}{message}\033[0m"

    # Configure root logger
    handler = logging.StreamHandler()
    formatter = ColorFormatter(
        "%(asctime)s | %(levelname)s | %(name)s | pid=%(process)d | tid=%(threadName)s | %(filename)s:%(lineno)d | %(funcName)s() | %(message)s"
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    # Example usage
    logger.info("This is green INFO")
    logger.error("This is red ERROR")


logger = logging.getLogger(__name__)

def field_typechecker(type_: Type[Any]):

    def inner_handler(instance, attribute, value):
        if not isinstance(value, type_):
            raise TypeError(
                f"Expected type {type_.__name__} for {instance.__class__.__name__}.{attribute.name}, got {type(value).__name__}"
            )

    return inner_handler


# def state_typechecker():
#     return field_typechecker(type_=WorkflowState)


def execute_safe(default_return=None, service_name: Optional[str] = None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if service_name:
                    logger.error(f"{service_name} error in {func.__name__}: {e}")
                else:
                    logger.error(f"Error in {func.__name__}: {e}")
                return default_return

        return wrapper

    return decorator


class GeneralPurposeSingletonMeta(type):
    __instances: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls.__instances:
            cls.__instances[cls] = super().__call__(*args, **kwargs)
        return cls.__instances[cls]
