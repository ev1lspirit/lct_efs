from abc import ABC, abstractmethod
from enum import Enum
from functools import wraps
import inspect
import logging
import re
from urllib.parse import urlparse
from attr import define, field
from typing import TYPE_CHECKING, Any, Callable, Optional, TypeVar
from simpleeval import simple_eval

from utils import dump_context

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

    @wraps(function)
    def wrapper(self, *args, **kwargs):
        if not isinstance(self, BaseHandler):
            raise TypeError(
                f"Expected {BaseHandler.__name__}, got {type(self).__name__}"
            )
        if hasattr(self.metadata, "dependent_variables"):
            if not all(
                var in self.context.session for var in self.metadata.dependent_variables
            ):
                missing_vars = [
                    var
                    for var in self.metadata.dependent_variables
                    if var not in self.context.session
                ]
                raise ValueError(
                    f"Missing dependent variables in context: {missing_vars}"
                )
        return function(self, *args, **kwargs)

    return wrapper


class BaseHandler(ABC):
    __slots__ = ("metadata", "context")
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

    def result(self):
        # Technical states should handle missing variables gracefully
        # They often check for variable existence/validity, so we don't enforce dependent_variables
        try:
            return simple_eval(
                self.metadata.expression, 
                names=self.context.session, 
                functions={"len": len, "sum": sum, "max": max, "min": min}
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

    def result(self):
        if self.behaviour_type == BehaviourTypeEnum.init:
            return self.init_result()
        elif self.behaviour_type == BehaviourTypeEnum.error:
            return self.error_result()
        else:
            raise ValueError(f"Unknown behaviour type: {self.behaviour_type}")

    def error_result(self):
        return

    def init_result(self):
        context_key = self.metadata.redis_client.get_wf_context_key(
            session_id=self.context._workflow_id
        )
        if not self.metadata.redis_client.r.exists(context_key):
            workflow_context = self.metadata.mongo_client.get(self.context._workflow_id)
            if not isinstance(workflow_context, dict):
                logger.error(f"Workflow context {self.context._workflow_id} not found")
                raise ValueError(f"Workflow context for {self.context._workflow_id} not found")

            wf_context_json = dump_context(workflow_context)
            self.metadata.redis_client.set_workflow_context(
                session_id=self.context._workflow_id, context=wf_context_json
            )
        else:
            workflow_context = self.metadata.redis_client.get_workflow_context(
                session_id=self.context._workflow_id
            )
        if not (workflow_context.keys() & self.context.session.keys()):
            with self.context as context:
                context.update(workflow_context)
        return workflow_context


@define(slots=True)
class IntegrationHandler(BaseHandler):
    adapter: Any  # CommonAdapter  # type: ignore[name-defined]
    metadata: "IntegrationStateExpression"
    context: "SessionContext"

    def _split_url(self, url=None):
        """Split URL into base_url and endpoint"""
        url_to_parse = url or self.metadata.url
        parsed = urlparse(url_to_parse)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        endpoint = parsed.path
        return base_url, endpoint

    def _get_method(self, adapter):
        method_attr = getattr(adapter, self.metadata.method, None)
        if method_attr is None:
            raise ValueError(f"Method {self.metadata.method} not found in adapter")
        return method_attr

    def _extract_variables(self, params: dict) -> list[str]:
        """Извлекает список переменных из params в формате {{variable}}"""
        pattern = r'\{\{(\w+)\}\}'
        variables = set()
        
        def extract_from_value(value):
            if isinstance(value, str):
                matches = re.findall(pattern, value)
                variables.update(matches)
            elif isinstance(value, dict):
                for v in value.values():
                    extract_from_value(v)
            elif isinstance(value, list):
                for item in value:
                    extract_from_value(item)
        
        for value in params.values():
            extract_from_value(value)
        
        return list(variables)

    def _interpolate_params(self, params: dict) -> dict:
        """Заменяет {{variable}} на значения из context.session"""
        pattern = r'\{\{(\w+)\}\}'
        
        def interpolate_value(value):
            if isinstance(value, str):
                # Находим все переменные в строке
                matches = re.findall(pattern, value)
                result = value
                for var_name in matches:
                    if var_name not in self.context.session:
                        raise ValueError(
                            f"Variable '{var_name}' not found in context. "
                            f"Available variables: {list(self.context.session.keys())}"
                        )
                    context_value = self.context.session[var_name]
                    # Заменяем {{var}} на значение
                    result = result.replace(f"{{{{{var_name}}}}}", str(context_value))
                return result
            elif isinstance(value, dict):
                return {k: interpolate_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [interpolate_value(item) for item in value]
            else:
                return value
        
        return {key: interpolate_value(value) for key, value in params.items()}

    @check_context_consistency
    def result(self):  # type: ignore
        # Интерполируем URL - заменяем {{variable}} в самом URL
        interpolated_url = self.metadata.url
        url_variables_found = []
        for match in re.finditer(r'\{\{(\w+)\}\}', self.metadata.url):
            var_name = match.group(1)
            url_variables_found.append(var_name)
            if var_name not in self.context.session:
                raise ValueError(
                    f"Variable '{var_name}' required in URL but not found in context. "
                    f"Available variables: {list(self.context.session.keys())}"
                )
            context_value = self.context.session[var_name]
            interpolated_url = interpolated_url.replace(f"{{{{{var_name}}}}}", str(context_value))
        
        if url_variables_found:
            logger.debug(f"URL variables interpolated: {url_variables_found}")
        
        base_url, endpoint = self._split_url(interpolated_url)
        logger.debug(f"Base URL: {base_url}, Endpoint: {endpoint}")
        
        # Интерполируем params или body в зависимости от метода
        method = self.metadata.method.lower()
        request_kwargs = {}
        
        if method in ['post', 'put', 'patch']:
            # POST/PUT/PATCH используют body (передается как json в requests)
            params_to_use = self.metadata.body or {}
            interpolated_params = self._interpolate_params(params_to_use)
            logger.info(f"Integration request: {self.metadata.method.upper()} {interpolated_url}")
            logger.debug(f"Original body: {self.metadata.body}")
            logger.debug(f"Interpolated body: {interpolated_params}")
            # Для POST/PUT/PATCH передаем данные как json, а не params
            request_kwargs['json'] = interpolated_params
        else:
            # GET/DELETE используют params (query string)
            params_to_use = self.metadata.params or {}
            interpolated_params = self._interpolate_params(params_to_use)
            logger.info(f"Integration request: {self.metadata.method.upper()} {interpolated_url}")
            logger.debug(f"Original params: {self.metadata.params}")
            logger.debug(f"Interpolated params: {interpolated_params}")
            request_kwargs['params'] = interpolated_params
        
        logger.debug(f"Request kwargs prepared: {list(request_kwargs.keys())}")
        
        adapter = self.adapter(base_url=base_url)
        method_attr = self._get_method(adapter)
        
        logger.info(f"Executing adapter method: {self.metadata.method.upper()}")
        response = method_attr(endpoint=endpoint, **request_kwargs)
        
        # Проверяем, является ли ответ ошибкой
        if hasattr(response, 'error') and response.error:
            logger.error(f"API request failed: {response.message}")
            if hasattr(response, 'status_code') and response.status_code:
                logger.error(f"Status code: {response.status_code}")
            if hasattr(response, 'content') and response.content:
                logger.debug(f"Error response content: {response.content}")
            
            # Если указана переменная для ошибки, сохраняем в контекст
            if self.metadata.error_variable:
                with self.context as ctx:
                    ctx[self.metadata.error_variable] = {
                        'error': True,
                        'message': response.message,
                        'status_code': getattr(response, 'status_code', None),
                        'content': getattr(response, 'content', None)
                    }
                logger.info(f"Error saved to context variable: {self.metadata.error_variable}")
            # Возвращаем ошибку вместо исключения для возможности обработки в workflow
            return response
        
        logger.info(f"Integration response received successfully: {type(response).__name__}")
        if isinstance(response, dict):
            logger.debug(f"Response keys: {list(response.keys())}")
        elif isinstance(response, list):
            logger.debug(f"Response is a list with {len(response)} items")
        
        return response


@define(slots=True)
class SubflowHandler(BaseHandler):
    """Handler for executing subflow (calling another workflow as subprocess)"""
    metadata: "SubflowStateExpression"
    context: "SessionContext"

    @check_context_consistency
    def result(self):
        """
        Execute subflow by creating a new automaton instance for the subflow workflow

        Returns:
            dict: Subflow execution result with status and output variables
        """
        from workflow_builder.automaton.automaton import Automaton
        from storage.redis.service import RedisCache
        import uuid
        import json

        logger.info(f"🔄 Starting subflow execution: {self.metadata.subflow_workflow_id}")

        # Create a new session for the subflow
        subflow_session_id = f"subflow_{uuid.uuid4().hex}"
        redis_cache = RedisCache()

        # Prepare subflow context by mapping parent variables to subflow variables
        subflow_context = {}
        if self.metadata.input_mapping:
            for subflow_var, parent_var in self.metadata.input_mapping.items():
                if parent_var not in self.context.session:
                    logger.warning(f"Parent variable '{parent_var}' not found in context for subflow input")
                    continue
                subflow_context[subflow_var] = self.context.session[parent_var]
                logger.debug(f"Mapped {parent_var} -> {subflow_var}: {subflow_context[subflow_var]}")

        # Store parent workflow info in subflow context for potential return
        subflow_context["__parent_workflow_id"] = self.context._workflow_id
        subflow_context["__parent_session_id"] = self.context._session_id
        subflow_context["__is_subflow"] = True

        logger.info(f"Subflow context prepared with {len(subflow_context)} variables")

        try:
            # Initialize subflow session in Redis
            subflow_context["__workflow_id"] = self.metadata.subflow_workflow_id
            redis_cache.init_session(subflow_session_id, subflow_context)
            logger.debug(f"Subflow session initialized: {subflow_session_id}")

            # Create and run the subflow automaton
            subflow_automaton = Automaton(
                session_id=subflow_session_id,
                workflow_id=self.metadata.subflow_workflow_id
            )

            logger.info(f"Executing subflow automaton...")
            subflow_result = subflow_automaton.run(event_name=None)

            # Retrieve final subflow context
            subflow_final_context = redis_cache.get_session(subflow_session_id)
            logger.info(f"Subflow completed successfully")

            # Map subflow output variables back to parent context
            if self.metadata.output_mapping:
                for parent_var, subflow_var in self.metadata.output_mapping.items():
                    if subflow_var in subflow_final_context:
                        with self.context as ctx:
                            ctx[parent_var] = subflow_final_context[subflow_var]
                        logger.debug(f"Mapped subflow output: {subflow_var} -> {parent_var}")
                    else:
                        logger.warning(f"Subflow variable '{subflow_var}' not found in subflow context")

            # Store subflow result
            result = {
                "status": "completed",
                "subflow_session_id": subflow_session_id,
                "final_state": subflow_result.get("current_state") if isinstance(subflow_result, dict) else None
            }

            logger.info(f"✅ Subflow execution completed: {self.metadata.subflow_workflow_id}")
            return result

        except Exception as e:
            logger.error(f"❌ Subflow execution failed: {str(e)}", exc_info=True)

            # Store error in error_variable if specified
            if self.metadata.error_variable:
                error_info = {
                    "error": True,
                    "message": str(e),
                    "subflow_workflow_id": self.metadata.subflow_workflow_id,
                    "subflow_session_id": subflow_session_id
                }
                with self.context as ctx:
                    ctx[self.metadata.error_variable] = error_info
                logger.info(f"Error saved to context variable: {self.metadata.error_variable}")

            return {
                "status": "failed",
                "error": str(e),
                "subflow_session_id": subflow_session_id
            }
        finally:
            # Cleanup: optionally delete subflow session from Redis
            # Commented out to allow debugging; enable if needed
            # redis_cache.delete_session(subflow_session_id)
            pass
