from functools import wraps
import hashlib
import json
from config import settings
import time
from typing import Any, Optional, Type
import logging
from bson.objectid import ObjectId


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


def call_deadlock_protection(start_time):
    if (time.time() - start_time) > settings.DEADLOCK_TIMEOUT:
        raise Exception("Deadlock detected. Aborting.")


def generate_screen_id(original_oid: ObjectId, unique_string: str) -> ObjectId:
    combined = str(original_oid) + unique_string
    hash_hex = hashlib.md5(combined.encode()).hexdigest()  # or sha256
    return ObjectId(hash_hex[:24])


def prepare_context_response(context: dict):
    if isinstance(context, (bytes, bytearray)):
        context = context.decode()
    if isinstance(context, str):
        return json.loads(context)
    
    def safe_decode_value(v):
        """Safely decode value from Redis - try JSON first, then plain decode"""
        if v.startswith(b"{") or v.startswith(b"["):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                # If JSON parsing fails, return as string
                return v.decode()
        return v.decode()
    
    return {
        k.decode(): safe_decode_value(v)
        for k, v in context.items()
    }

def _convert_bools_to_str(obj):
    """Recursively convert all bool and None values to strings in nested structures."""
    if obj is None:
        return "None"
    elif isinstance(obj, bool):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: _convert_bools_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_bools_to_str(item) for item in obj]
    else:
        return obj

def dump_context(context_data: dict) -> dict:
    """
    Dumps the context data to a JSON-serializable format.
    Converts all boolean and None values (including nested ones) to strings for Redis compatibility.

    Args:
        context_data (dict): The context data to dump.

    Returns:
        dict: The dumped context data.
    """
    dumped_context = {}
    for key, value in context_data.items():
        if isinstance(key, (bytes, bytearray)):
            key = key.decode()
        
        # Skip None values at top level or convert to string
        if value is None:
            dumped_context[key] = "None"
        elif isinstance(value, (dict, list)):
            # Convert bools and None recursively before JSON serialization
            value = _convert_bools_to_str(value)
            dumped_context[key] = json.dumps(value)
        elif isinstance(value, bool):
            # Convert bool to string for Redis compatibility
            dumped_context[key] = str(value)
        else:
            dumped_context[key] = value.decode() if isinstance(value, (bytes, bytearray)) else value
    return dumped_context

class GeneralPurposeSingletonMeta(type):
    __instances: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls.__instances:
            cls.__instances[cls] = super().__call__(*args, **kwargs)
        return cls.__instances[cls]


class AmbiguityFreeList(list):

    def __init__(self):
        super().__init__()
        self.unique_items_set = set()

    def append(self, object: Any) -> None:
        if object in self.unique_items_set:
            raise ValueError(f"Duplicate item found. One expression seems to be overwriting the result of other expression with the same state. Original: {self}  Extension: {object}")
        self.unique_items_set.add(object)
        return super().append(object)

    def extend(self, iterable) -> None:
        if any(item in self.unique_items_set for item in iterable):
            raise ValueError(f"Duplicate item found in iterable. One expression seems to be overwriting the result of other expression with the same state. Original: {self}  Extension: {iterable}")
        self.unique_items_set.update(iterable)
        return super().extend(iterable)
