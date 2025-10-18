from abc import ABC, abstractmethod
from enum import Enum
from functools import wraps
import asyncio
import inspect
import logging
from urllib.parse import urlparse
from attr import define, field
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Optional, TypeVar
from simpleeval import simple_eval

from adapters.commonAdapter import APIError
from utils import dump_context
from workflow_builder.mixins import ParameterInterpolationMixin

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from context import SessionContext
    from workflow_builder.expressions import (
        IntegrationStateExpression,
        TechnicalStateExpression,
        ScreenStateExpression,
        ServiceStateExpression,
    )

HandlerClass = TypeVar("HandlerClass")


class BehaviourTypeEnum(str, Enum):
    init = "init"
    error = "error"


def check_context_consistency(function: Callable):
    func_sig = inspect.signature(function)
    if "self" not in func_sig.parameters:
        raise ValueError("Function must be a method")

    async def _shared_logic(self):
        if not isinstance(self, BaseHandler):
            raise TypeError(
                f"Expected {BaseHandler.__name__}, got {type(self).__name__}"
            )
        session = await self.context.session()
        if hasattr(self.metadata, "dependent_variables"):
            if not all(
                var in session for var in self.metadata.dependent_variables
            ):
                missing_vars = [
                    var
                    for var in self.metadata.dependent_variables
                    if var not in session
                ]
                raise ValueError(
                    f"Missing dependent variables in context: {missing_vars}"
                )

    if inspect.iscoroutinefunction(function):

        @wraps(function)
        async def wrapper_async(self, *args, **kwargs):
            await _shared_logic(self)
            return await function(self, *args, **kwargs)

        return wrapper_async

    @wraps(function)
    def wrapper(self, *args, **kwargs):
        _shared_logic(self)
        return function(self, *args, **kwargs)

    return wrapper


@define(slots=True)
class BaseHandler(ABC):
    metadata: Any
    context: "SessionContext"

    @abstractmethod
    def result(self) -> Any:
        raise NotImplementedError


@define(slots=True)
class ScreenHandler(BaseHandler):
    metadata: "ScreenStateExpression"
    context: "SessionContext"

    def result(self, event_name: Optional[str] = None) -> bool:
        """Проверяет, совпадает ли переданное событие с событием в metadata"""
        if event_name is None:
            return False
        return self.metadata.event_name == event_name


@define(slots=True)
class TechnicalHandler(BaseHandler):
    metadata: "TechnicalStateExpression"
    context: "SessionContext"

    async def result(self):
        # Technical states should handle missing variables gracefully
        # They often check for variable existence/validity, so we don't enforce dependent_variables
        context = await self.context.session()
        try:
            return simple_eval(
                self.metadata.expression,
                names=context,
                functions={"len": len, "sum": sum, "max": max, "min": min},
            )
        except Exception as e:
            # If variable doesn't exist, treat as validation failure (False)
            # simple_eval may throw various exceptions for undefined variables
            logger.warning(
                f"Error evaluating technical expression '{self.metadata.expression}': {type(e).__name__}: {e}. "
                "Treating as validation failure (False)."
            )
            return False


@define(slots=True)
class DependencyHandler(BaseHandler):
    metadata: "ServiceStateExpression"
    context: "SessionContext"
    behaviour_type: BehaviourTypeEnum = field(default=BehaviourTypeEnum.init)

    async def result(self):
        if self.behaviour_type == BehaviourTypeEnum.init:
            return await self.init_result()
        elif self.behaviour_type == BehaviourTypeEnum.error:
            return self.error_result()
        else:
            raise ValueError(f"Unknown behaviour type: {self.behaviour_type}")

    def error_result(self):
        return

    async def init_result(self):
        context_key = self.metadata.redis_client.workflow_context_key(
            session_id=self.context._workflow_id
        )
        if not await self.metadata.redis_client.redis.exists(context_key):
            workflow_context = self.metadata.mongo_client.get(self.context._workflow_id)

            if not isinstance(workflow_context, dict):
                logger.error(f"Workflow context {self.context._workflow_id} not found in MongoDB")
                raise ValueError(
                    f"Workflow context for {self.context._workflow_id} not found"
                )

            # Сохраняем в Redis для будущих запросов (асинхронно, не ждём результата)
            wf_context_json = dump_context(workflow_context)
            await self.metadata.redis_client.set_workflow_context(
                session_id=self.context._workflow_id, context=wf_context_json
            )
            logger.debug(f"Saved workflow context to Redis: {self.context._workflow_id}")
        else:
            workflow_context = await self.metadata.redis_client.get_workflow_context(
                session_id=self.context._workflow_id
            )
        context = await self.context.session()
        if not (workflow_context.keys() & context.keys()):
            async with self.context as context:
                context.update(workflow_context)
        return workflow_context


@define(slots=True)
class IntegrationHandler(ParameterInterpolationMixin, BaseHandler):
    adapter: Any  # CommonAdapter  # type: ignore[name-defined]
    metadata: Any
    context: "SessionContext"

    def _split_url(self, url=None):
        """Split URL into base_url and endpoint"""
        url_to_parse = url or self.metadata.url
        parsed = urlparse(url_to_parse)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        endpoint = parsed.path
        return base_url, endpoint

    def _get_method(self, adapter) -> Callable[[str, Any], Awaitable]:
        method_attr = getattr(adapter, self.metadata.method, None)
        if method_attr is None:
            raise ValueError(f"Method {self.metadata.method} not found in adapter")
        return method_attr

    async def __process_api_error(self, response: APIError):
        logger.error(f"API request failed: {response.message}")
        if response.status_code:
            logger.error(f"Status code: {response.status_code}")
        if response.content:
            logger.debug(f"Error response content: {response.content}")

        # Если указана переменная для ошибки, сохраняем в контекст
        if self.metadata.error_variable:
            async with self.context as ctx:
                ctx[self.metadata.error_variable] = response.model_dump()
            logger.info(
                f"Error saved to context variable: {self.metadata.error_variable}"
            )
        # Возвращаем ошибку вместо исключения для возможности обработки в workflow
        return response

    async def __process_response(self, response):
        # Проверяем, является ли ответ ошибкой
        if isinstance(response, APIError):
            return await self.__process_api_error(response)
        logger.info(
            f"Integration response received successfully: {type(response).__name__}"
        )
        if isinstance(response, dict):
            logger.debug(f"Response keys: {list(response.keys())}")
        elif isinstance(response, list):
            logger.debug(f"Response is a list with {len(response)} items")

        return response

    @check_context_consistency
    async def result(self):  # type: ignore
        context = await self.context.session()
        interpolated_url = self.interpolate_url(context)
        base_url, endpoint = self._split_url(interpolated_url)
        logger.info(f"Base URL: {base_url}, Endpoint: {endpoint}")

        request_kwargs = self.interpolate_params(interpolated_url, context)
        adapter = self.adapter(base_url=base_url)
        method_ = self._get_method(adapter)
        logger.info(f"Executing adapter method: {self.metadata.method.upper()}")
        response = await method_(endpoint=endpoint, **request_kwargs)
        return await self.__process_response(response)
