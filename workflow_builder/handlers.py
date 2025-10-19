from abc import ABC, abstractmethod
from enum import Enum
from functools import wraps
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
        TechnicalStateExpression,
        ScreenStateExpression,
        ServiceStateExpression
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
        import time
        
        start_time = time.time()
        expected_event = self.metadata.event_name
        logger.info(f"[SCREEN_TIMING] ▶️ Checking screen event: expected='{expected_event}', received='{event_name}'")
        
        if event_name is None:
            logger.info(f"[SCREEN_TIMING] ❌ No event provided")
            elapsed = (time.time() - start_time) * 1000
            logger.info(f"[SCREEN_TIMING] ⏱️ Total time: {elapsed:.2f}ms")
            return False
        
        result = self.metadata.event_name == event_name
        elapsed = (time.time() - start_time) * 1000
        
        if result:
            logger.info(f"[SCREEN_TIMING] ✅ Event matched!")
        else:
            logger.info(f"[SCREEN_TIMING] ❌ Event mismatch")
        
        logger.info(f"[SCREEN_TIMING] ⏱️ Total time: {elapsed:.2f}ms")
        return result


@define(slots=True)
class TechnicalHandler(BaseHandler):
    metadata: "TechnicalStateExpression"
    context: "SessionContext"

    async def result(self):
        import time
        
        # [TECHNICAL_TIMING] Начало выполнения технического состояния
        start_time = time.time()
        variable_name = self.metadata.variable
        logger.info(f"[TECHNICAL_TIMING] ▶️ Evaluating technical expression for variable: '{variable_name}'")
        logger.info(f"[TECHNICAL_TIMING] Expression: {self.metadata.expression}")
        logger.info(f"[TECHNICAL_TIMING] Dependent variables: {self.metadata.dependent_variables}")
        
        # Technical states should handle missing variables gracefully
        # They often check for variable existence/validity, so we don't enforce dependent_variables
        context = await self.context.session()
        try:
            result = simple_eval(
                self.metadata.expression,
                names=context,
                functions={"len": len, "sum": sum, "max": max, "min": min},
            )
            elapsed = (time.time() - start_time) * 1000
            logger.info(f"[TECHNICAL_TIMING] ✅ Expression evaluated successfully: {result}")
            logger.info(f"[TECHNICAL_TIMING] ⏱️ Total time: {elapsed:.2f}ms")
            return result
        except Exception as e:
            # If variable doesn't exist, treat as validation failure (False)
            # simple_eval may throw various exceptions for undefined variables
            elapsed = (time.time() - start_time) * 1000
            logger.warning(
                f"[TECHNICAL_TIMING] ⚠️ Error evaluating expression '{self.metadata.expression}': "
                f"{type(e).__name__}: {e}. Treating as validation failure (False)."
            )
            logger.info(f"[TECHNICAL_TIMING] ⏱️ Total time: {elapsed:.2f}ms")
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
        import time
        
        # [SERVICE_TIMING] Начало выполнения служебного состояния
        start_time = time.time()
        workflow_id = self.context._workflow_id
        logger.info(f"[SERVICE_TIMING] ▶️ Initializing service for workflow: {workflow_id}")
        
        context_key = self.metadata.redis_client.workflow_context_key(
            session_id=self.context._workflow_id
        )
        
        # Проверка Redis
        redis_check_start = time.time()
        redis_exists = await self.metadata.redis_client.redis.exists(context_key)
        redis_check_elapsed = (time.time() - redis_check_start) * 1000
        logger.info(f"[SERVICE_TIMING] ⏱️ Redis check: {redis_check_elapsed:.2f}ms (exists={redis_exists})")
        
        if not redis_exists:
            # Загрузка из MongoDB
            mongo_start = time.time()
            workflow_context = self.metadata.mongo_client.get(self.context._workflow_id)
            mongo_elapsed = (time.time() - mongo_start) * 1000
            logger.info(f"[SERVICE_TIMING] ⏱️ MongoDB read: {mongo_elapsed:.2f}ms")

            if not isinstance(workflow_context, dict):
                logger.error(f"[SERVICE_TIMING] ❌ Workflow context {self.context._workflow_id} not found in MongoDB")
                raise ValueError(
                    f"Workflow context for {self.context._workflow_id} not found"
                )

            # Сохраняем в Redis
            redis_save_start = time.time()
            wf_context_json = dump_context(workflow_context)
            await self.metadata.redis_client.set_workflow_context(
                session_id=self.context._workflow_id, context=wf_context_json
            )
            redis_save_elapsed = (time.time() - redis_save_start) * 1000
            logger.info(f"[SERVICE_TIMING] ⏱️ Redis save: {redis_save_elapsed:.2f}ms")
            logger.info(f"[SERVICE_TIMING] 💾 Saved workflow context to Redis: {self.context._workflow_id}")
        else:
            # Загрузка из Redis
            redis_read_start = time.time()
            workflow_context = await self.metadata.redis_client.get_workflow_context(
                session_id=self.context._workflow_id
            )
            redis_read_elapsed = (time.time() - redis_read_start) * 1000
            logger.info(f"[SERVICE_TIMING] ⏱️ Redis read: {redis_read_elapsed:.2f}ms")
        
        # Обновление контекста сессии
        update_start = time.time()
        context = await self.context.session()
        if not (workflow_context.keys() & context.keys()):
            async with self.context as context:
                context.update(workflow_context)
        update_elapsed = (time.time() - update_start) * 1000
        logger.info(f"[SERVICE_TIMING] ⏱️ Context update: {update_elapsed:.2f}ms")
        
        total_elapsed = (time.time() - start_time) * 1000
        logger.info(f"[SERVICE_TIMING] ✅ Service initialization completed")
        logger.info(f"[SERVICE_TIMING] ⏱️ Total time: {total_elapsed:.2f}ms")
        
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
        import time
        
        # [INTEGRATION_TIMING] Начало выполнения интеграции
        start_time = time.time()
        variable_name = self.metadata.variable
        logger.info(f"[INTEGRATION_TIMING] ▶️ Starting integration for variable: '{variable_name}'")
        logger.info(f"[INTEGRATION_TIMING] Original URL: {self.metadata.url}")
        logger.info(f"[INTEGRATION_TIMING] Method: {self.metadata.method.upper()}")
        
        # Получаем контекст
        context_start = time.time()
        context = await self.context.session()
        context_elapsed = (time.time() - context_start) * 1000
        logger.info(f"[INTEGRATION_TIMING] ⏱️ Context retrieval: {context_elapsed:.2f}ms")
        
        # Интерполяция URL
        interpolation_start = time.time()
        variable_interpolated_url = self.context_interpolation(
            url=self.metadata.url, session=context
        )
        interpolated_url = self.interpolate_url(
            url=variable_interpolated_url, session=context
        )
        interpolation_elapsed = (time.time() - interpolation_start) * 1000
        logger.info(f"[INTEGRATION_TIMING] ⏱️ URL interpolation: {interpolation_elapsed:.2f}ms")
        logger.info(f"[INTEGRATION_TIMING] Interpolated URL: {interpolated_url}")

        base_url, endpoint = self._split_url(interpolated_url)
        logger.info(f"[INTEGRATION_TIMING] Base URL: {base_url}")
        logger.info(f"[INTEGRATION_TIMING] Endpoint: {endpoint}")

        # Интерполяция параметров
        params_start = time.time()
        request_kwargs = self.interpolate_params(interpolated_url, context)
        params_elapsed = (time.time() - params_start) * 1000
        logger.info(f"[INTEGRATION_TIMING] ⏱️ Params interpolation: {params_elapsed:.2f}ms")
        
        # Логируем параметры запроса (безопасно)
        if 'json' in request_kwargs:
            logger.info(f"[INTEGRATION_TIMING] Request body keys: {list(request_kwargs['json'].keys())}")
        if 'params' in request_kwargs:
            logger.info(f"[INTEGRATION_TIMING] Query params: {list(request_kwargs['params'].keys())}")
        
        # Выполнение HTTP запроса
        adapter = self.adapter(base_url=base_url)
        method_ = self._get_method(adapter)
        
        http_start = time.time()
        logger.info(f"[INTEGRATION_TIMING] 🌐 Executing HTTP {self.metadata.method.upper()} request...")
        response = await method_(endpoint=endpoint, **request_kwargs)
        http_elapsed = (time.time() - http_start) * 1000
        logger.info(f"[INTEGRATION_TIMING] ⏱️ HTTP request: {http_elapsed:.2f}ms")
        
        # Обработка ответа
        process_start = time.time()
        result = await self.__process_response(response)
        process_elapsed = (time.time() - process_start) * 1000
        logger.info(f"[INTEGRATION_TIMING] ⏱️ Response processing: {process_elapsed:.2f}ms")
        
        # Общее время
        total_elapsed = (time.time() - start_time) * 1000
        logger.info(f"[INTEGRATION_TIMING] ✅ Integration completed for '{variable_name}'")
        logger.info(f"[INTEGRATION_TIMING] 📊 Total time: {total_elapsed:.2f}ms")
        logger.info(f"[INTEGRATION_TIMING] 📊 Breakdown: context={context_elapsed:.2f}ms, "
                   f"url_interp={interpolation_elapsed:.2f}ms, "
                   f"params_interp={params_elapsed:.2f}ms, "
                   f"http={http_elapsed:.2f}ms, "
                   f"processing={process_elapsed:.2f}ms")
        
        return result
