from abc import ABC, abstractmethod
from functools import partial
from attr import define, field
from typing import Any, TypeVar

from fastapi import dependencies
from context import SessionContext
from workflow_builder.transitions import Transition


HandlerClass = TypeVar("HandlerClass")


class Expression:
    """ Helper class to create state expressions"""

    @classmethod
    def technical(cls, *, dependent_variables: list[str], expression: str) -> 'TechnicalStateExpression':
        return TechnicalStateExpression(
            dependent_variables=dependent_variables,
            expression=expression
        )

    @classmethod
    def integration(cls, *, variable: str, url: str, params: dict[str, Any],  method: str = "get") -> 'IntegrationStateExpression':
        return IntegrationStateExpression(
            variable=variable, url=url, params=params, method=method
        )

@define
class BaseStateExpression:
    _transition_bind: str = field(default=None, init=False)  # state id to bind after execution
    _transition_bind_object: Any = field(default=None, init=False)

    @property
    def transition_bind_object(self) -> Transition:
        return self._transition_bind_object

    @property
    def transition_bind(self) -> str:
        return self._transition_bind

    @transition_bind_object.setter
    def transition_bind_object(self, transition: Transition):
        if transition.state_id != self.transition_bind:
            raise ValueError(f"Transition destination {transition.state_id} does not match bind id {self.transition_bind}")
        self._transition_bind_object = transition

    def bind_transition(self, name: str):
        if self._transition_bind is not None:
            raise ValueError("Transition already bound")
        self._transition_bind = name
        return self


@define
class TechnicalStateExpression(BaseStateExpression):
    #variable: str  # variable to be updated
    dependent_variables: list[str] # a list of dependent variables
    expression: str  # python execution lambda


@define
class IntegrationStateExpression(BaseStateExpression):
    variable: str = field()  # variable to be updated
    url: str = field()  # endpoint URL
    params: dict[str, Any] = field(default={})  # query or body params
    method: str = field(default="get")  # GET, POST, etc.


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
            missing_vars = [var for var in self.metadata.dependent_variables if var not in self.context]
            raise ValueError(f"Missing dependent variables in context: {missing_vars}")
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
        # TODO: handle response
        # 1) Матчинг с контекстом
        
        return response
