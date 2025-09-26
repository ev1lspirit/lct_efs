from functools import wraps
from attr import define, field
from typing import Any, Union
from workflow_builder.transitions import Transition


@define
class BaseStateExpression:
    _transition_bind: str = field(
        default=None, init=False
    )  # state id to bind after execution
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
            raise ValueError(
                f"Transition destination {transition.state_id} does not match bind id {self.transition_bind}"
            )
        self._transition_bind_object = transition

    def bind_transition(self, name: str):
        if self.transition_bind is not None:
            raise ValueError("Transition already bound")
        self._transition_bind = name
        return self


class LogicalExpressionMixin:

    def __process_dependent_vars(self, value):
        dependent_vars = []
        dependent_vars.extend(self.dependent_variables)
        dependent_vars.extend(value.dependent_variables)
        return dependent_vars

    def __process_expressions(self, value):
        expressions = []
        self_expression = self.expression
        value_expression = value.expression
        if isinstance(self_expression, str):
            self_expression = [self_expression]
        if isinstance(value_expression, str):
            value_expression = [value_expression]

        expressions.extend(self_expression)
        expressions.extend(value_expression)
        return expressions

    @staticmethod
    def _value_field_check(function):

        @wraps(function)
        def wrapper(self, value):
            if not isinstance(value, TechnicalStateExpression):
                raise TypeError(
                    f"Expected TechnicalStateExpression, got f{type(value).__name__}"
                )
            if self.transition_bind is not None or value.transition_bind is not None:
                raise ValueError("Transition already bound")
            return function(self, value)

        return wrapper

    @_value_field_check
    def __or__(self, value) -> "TechnicalOrExpression":
        dependent_vars = self.__process_dependent_vars(value)
        expressions = self.__process_expressions(value)
        return TechnicalOrExpression(
            dependent_vars=dependent_vars, expressions=expressions
        )

    @_value_field_check
    def __and__(self, value: Any) -> "TechnicalAndExpression":
        dependent_vars = self.__process_dependent_vars(value)
        expressions = self.__process_expressions(value)
        return TechnicalAndExpression(
            dependent_vars=dependent_vars, expressions=expressions
        )


@define(slots=True)
class TechnicalStateExpression(LogicalExpressionMixin, BaseStateExpression):
    # variable: str  # variable to be updated
    dependent_variables: list[str]  # a list of dependent variables
    expression: Union[str, list[str]]  # python execution lambda


@define(slots=True)
class IntegrationStateExpression(BaseStateExpression):
    variable: str = field()  # variable to be updated
    url: str = field()  # endpoint URL
    params: dict[str, Any] = field(default={})  # query or body params
    method: str = field(default="get")  # GET, POST, etc.


class Expression:
    """Helper class to create state expressions"""

    @classmethod
    def technical(
        cls, *, dependent_variables: list[str], expression: str
    ) -> "TechnicalStateExpression":
        return TechnicalStateExpression(
            dependent_variables=dependent_variables, expression=expression
        )

    @classmethod
    def integration(
        cls, *, variable: str, url: str, params: dict[str, Any], method: str = "get"
    ) -> "IntegrationStateExpression":
        return IntegrationStateExpression(
            variable=variable, url=url, params=params, method=method
        )


class TechnicalAndExpression(LogicalExpressionMixin, BaseStateExpression):
    __slots__ = ("dependent_variables", "expression")

    def __init__(self, dependent_vars, expressions):
        self.dependent_variables = dependent_vars
        self.expression = expressions
        super().__init__()


class TechnicalOrExpression(LogicalExpressionMixin, BaseStateExpression):
    __slots__ = ("dependent_variables", "expression")
    
    def __init__(self, dependent_vars, expressions):
        self.dependent_variables = dependent_vars
        self.expression = expressions
        super().__init__()
