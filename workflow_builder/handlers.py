from abc import ABC, abstractmethod
from attr import define
from typing import Any, TypeVar
from workflow_builder.expressions import (
    IntegrationStateExpression,
    TechnicalAndExpression,
    TechnicalOrExpression,
    TechnicalStateExpression,
)


HandlerClass = TypeVar("HandlerClass")


class BaseHandler(ABC):
    __slots__ = ("metadata", "context")
    metadata: Any
    context: dict[str, Any]

    @abstractmethod
    def result(self):
        raise NotImplementedError


@define
class TechnicalHandler:
    metadata: TechnicalStateExpression
    context: dict[str, Any]

    def result(self):
        if not all(var in self.context for var in self.metadata.dependent_variables):
            missing_vars = [
                var
                for var in self.metadata.dependent_variables
                if var not in self.context
            ]
            raise ValueError(f"Missing dependent variables in context: {missing_vars}")
        if isinstance(self.metadata, TechnicalAndExpression):
            return all(
                eval(expr, locals=self.context) for expr in self.metadata.expression
            )
        if isinstance(self.metadata, TechnicalOrExpression):
            return any(
                eval(expr, locals=self.context) for expr in self.metadata.expression
            )
        return eval(self.metadata.expression, locals=self.context)


@define
class IntegrationHandler:
    adapter: Any  # CommonAdapter  # type: ignore[name-defined]
    metadata: IntegrationStateExpression
    context: dict[str, Any]

    def result(self):
        adapter = self.adapter(url=self.metadata.url)
        response = adapter.request(
            method=self.metadata.method, params=self.metadata.params
        )
        return response
