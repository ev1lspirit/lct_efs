from abc import ABC, abstractmethod
from functools import wraps
import inspect
from attr import define
from typing import Any, Callable, TypeVar
from workflow_builder.expressions import (
    IntegrationStateExpression,
    TechnicalAndExpression,
    TechnicalOrExpression,
    TechnicalStateExpression,
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
        if not all(var in self.context for var in self.metadata.dependent_variables):
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
    context: dict[str, Any]

    @abstractmethod
    def result(self) -> Any:
        raise NotImplementedError


@define
class TechnicalHandler(BaseHandler):
    metadata: TechnicalStateExpression
    context: dict[str, Any]

    @check_context_consistency
    def result(self):
        if isinstance(self.metadata, TechnicalAndExpression):
            return all(
                eval(expr, locals=self.context) for expr in self.metadata.expression
            )
        if isinstance(self.metadata, TechnicalOrExpression):
            return any(
                eval(expr, locals=self.context) for expr in self.metadata.expression
            )
        return eval(self.metadata.expression, locals=self.context)


@define(slots=True)
class IntegrationHandler(BaseHandler):
    adapter: Any  # CommonAdapter  # type: ignore[name-defined]
    metadata: IntegrationStateExpression
    context: dict[str, Any]

    @check_context_consistency
    def result(self): # type: ignore
        adapter = self.adapter(url=self.metadata.url)
        response = adapter.request(
            method=self.metadata.method, params=self.metadata.params
        )
        return response
