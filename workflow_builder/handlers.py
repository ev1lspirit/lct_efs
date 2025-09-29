from abc import ABC, abstractmethod
from functools import wraps
import inspect
from urllib.parse import urlparse
from attr import define
from typing import TYPE_CHECKING, Any, Callable, Optional, TypeVar
from simpleeval import simple_eval

from context import SessionContext
from fsm import base

if TYPE_CHECKING:
    from workflow_builder.expressions import (
        IntegrationStateExpression,
        TechnicalStateExpression,
        ScreenStateExpression,
    )

HandlerClass = TypeVar("HandlerClass")


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
            if not all(var in self.context.session for var in self.metadata.dependent_variables):
                missing_vars = [
                    var
                    for var in self.metadata.dependent_variables
                    if var not in self.context
                ]
                raise ValueError(f"Missing dependent variables in context: {missing_vars}")
        return function(self, *args, **kwargs)

    return wrapper


class BaseHandler(ABC):
    __slots__ = ("metadata", "context")
    metadata: Any
    context: SessionContext

    @abstractmethod
    def result(self) -> Any:
        raise NotImplementedError


@define(slots=True)
class ScreenHandler(BaseHandler):
    metadata: 'ScreenStateExpression'
    context: SessionContext

    def result(self, event_name: Optional[str] = None) -> bool:
        """Проверяет, совпадает ли переданное событие с событием в metadata"""
        if event_name is None:
            return False
        return self.metadata.event_name == event_name

@define(slots=True)
class TechnicalHandler(BaseHandler):
    metadata: 'TechnicalStateExpression'
    context: SessionContext

    @check_context_consistency
    def result(self):
        # if isinstance(self.metadata, TechnicalAndExpression):
        #     return all(
        #         simple_eval(expr, names=self.context)
        #         for expr in self.metadata.expression
        #     )
        # if isinstance(self.metadata, TechnicalOrExpression):
        #     return any(
        #         simple_eval(expr, names=self.context)
        #         for expr in self.metadata.expression
        #     )
        return simple_eval(self.metadata.expression, names=self.context.session)


@define(slots=True)
class IntegrationHandler(BaseHandler):
    adapter: Any  # CommonAdapter  # type: ignore[name-defined]
    metadata: 'IntegrationStateExpression'
    context: SessionContext

    def _split_url(self):
        parsed = urlparse(self.metadata.url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        endpoint = parsed.path
        return base_url, endpoint

    def _get_method(self, adapter):
        method_attr = getattr(adapter, self.metadata.method, None)
        if method_attr is None:
            raise ValueError(f"Method {self.metadata.method} not found in adapter")
        return method_attr

    @check_context_consistency
    def result(self): # type: ignore
        base_url, endpoint = self._split_url()
        adapter = self.adapter(base_url=base_url)
        method_attr = self._get_method(adapter)
        response = method_attr(endpoint=endpoint, params=self.metadata.params)
        return response
