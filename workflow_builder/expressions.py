from functools import wraps
from attr import define, field
from functools import partial
from typing import Any, Callable
from workflow_builder.transitions import Transition


# def typeassert(function: Callable = None, types: list[type] = []):
#     if function is None:
#         return partial(typeassert, types=types)
#     @wraps(function)
#     def wrapper(instance, attribute, value):
#         for type_ in types:
#             if not isinstance(value, type_):
#                 raise TypeError(
#                     f"Expected type {type_.__name__} for {function.__name__}, got {type(arg).__name__}"
#                 )
#         return True
#     return wrapper

@define
class BaseStateExpression:
    """
    Base class for all state expressions
    It is not intended to be used directly

    BaseStateExpression is the base class for all state expressions
    It provides common attributes and methods for all state expressions
    Subclasses should override the execute method to provide their own implementation

    Attributes:
        transition_bind (str): state id to bind after execution
        transition_bind_object (Transition): transition object to bind after execution

    Methods:
        bind_transition (str): bind transition to expression
        execute (SessionContext, **kwargs): execute expression (must be overridden by subclasses)
    """
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

    @transition_bind.setter
    def transition_bind(self, value: str):
        if self._transition_bind is not None:
            raise ValueError("Transition already bound")
        if value is None:
            raise ValueError("Transition bind cannot be None")
        self._transition_bind = value

    @transition_bind_object.setter
    def transition_bind_object(self, transition: Transition):
        if not isinstance(transition, Transition):
            raise ValueError(f"Expected Transition, got {type(transition).__name__}")
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
    """
    A mixin class to provide common attributes and methods for logical state expressions

    It provides the following attributes and methods:

    Attributes:
        dependent_variables (list[str]): list of variables that the expression depends on

    Methods:
        __process_dependent_vars (value): processes dependent variables from the given value
        __process_expressions (value): processes expressions from the given value

    Subclasses should override the execute method to provide their own implementation

    """

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
    """
    Technical state expression

    TechnicalStateExpression is a class that represents a state expression
    that updates a technical state variable

    Attributes:
        variable (str): variable to be updated
        dependent_variables (list[str]): a list of dependent variables
        expression (Union[str, list[str]]): python execution lambda

    Methods:
        execute (SessionContext, **kwargs): execute expression (must be overridden by subclasses)

    Examples:
        >>> from workflow_builder.expressions import Expression
        >>> expr = Expression.technical(dependent_variables=["balance"], expression="balance>0")
        >>> expr.variable
        'balance'
        >>> expr.dependent_variables
        ['balance']
        >>> expr.expression
        'balance>0'

    Notes:
        TechnicalStateExpression is a subclass of BaseStateExpression
    """
    # variable: str  # variable to be updated
    dependent_variables: list[str]  # a list of dependent variables
    expression: str = field()  # python execution lambda

@define(slots=True)
class ScreenStateExpression(BaseStateExpression):
    """
    Screen state expression

    ScreenStateExpression is a class that represents a state expression
    that updates a screen state variable

    Attributes:
        event_name (str): event name to be triggered

    Methods:
        execute (SessionContext, **kwargs): execute expression (must be overridden by subclasses)

    Examples:
        >>> from workflow_builder.expressions import Expression
        >>> expr = Expression.event(event_name="submit")
        >>> expr.event_name
        'submit'
    """
    event_name: str = field()

@define(slots=True)
class IntegrationStateExpression(BaseStateExpression):
    """
    Integration state expression

    IntegrationStateExpression is a class that represents a state expression
    that updates an integration state variable

    Attributes:
        variable (str): variable to be updated
        url (str): endpoint URL
        params (dict[str, Any]): query or body params
        method (str): GET, POST, etc

    Methods:
        execute (SessionContext, **kwargs): execute expression (must be overridden by subclasses)

    Examples:
        >>> from workflow_builder.expressions import Expression
        >>> expr = Expression.integration(variable="z", url="http://example.com", params={"param": "value"})
        >>> expr.variable
        'z'
        >>> expr.url
        'http://example.com'
        >>> expr.params
        {'param': 'value'}

    Notes:
        IntegrationStateExpression is a subclass of BaseStateExpression
    """
    variable: str = field()
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

    @classmethod
    def event(
        cls, *, event_name: str
    ):
        return ScreenStateExpression(event_name=event_name)


class TechnicalAndExpression(LogicalExpressionMixin, BaseStateExpression):
    """
    TechnicalAndExpression is a logical expression that represents
    a conjunction of expressions. It is a subclass of BaseStateExpression
    and LogicalExpressionMixin.

    Attributes:
        dependent_variables (list[str]): a list of dependent variables
        expression (list[Union[str, list[str]]]): a list of python execution lambda

    Methods:
        execute (SessionContext, **kwargs): execute expression (must be overridden by subclasses)

    Notes:
        TechnicalAndExpression is a subclass of BaseStateExpression
        and LogicalExpressionMixin. It represents a logical AND operation
        between multiple expressions.

    Examples:
        >>> from workflow_builder.expressions import Expression
        >>> expr = Expression.technical(dependent_variables=["balance"], expression="balance>0") & Expression.technical(dependent_variables=["x"], expression="x>0")
        >>> expr.variable
        'balance'
        >>> expr.dependent_variables
        ['balance', 'x']
        >>> expr.expression
        ['balance>0', 'x>0']

    """
    __slots__ = ("dependent_variables", "expression")

    def __init__(self, dependent_vars, expressions):
        self.dependent_variables = dependent_vars
        self.expression = expressions
        super().__init__()


class TechnicalOrExpression(LogicalExpressionMixin, BaseStateExpression):
    """
    TechnicalOrExpression is a logical expression that represents
    a disjunction of expressions. It is a subclass of BaseStateExpression
    and LogicalExpressionMixin.

    Attributes:
        dependent_variables (list[str]): a list of dependent variables
        expression (list[Union[str, list[str]]]): a list of python execution lambda

    Methods:
        execute (SessionContext, **kwargs): execute expression (must be overridden by subclasses)

    Notes:
        TechnicalOrExpression is a subclass of BaseStateExpression
        and LogicalExpressionMixin. It represents a logical OR operation
        between multiple expressions.

    Examples:
        >>> from workflow_builder.expressions import Expression
        >>> expr = Expression.technical(dependent_variables=["balance"], expression="balance>0") | Expression.technical(dependent_variables=["x"], expression="x>0")
        >>> expr.variable
        'balance'
        >>> expr.dependent_variables
        ['balance', 'x']
        >>> expr.expression
        ['balance>0', 'x>0']

    """
    __slots__ = ("dependent_variables", "expression")

    def __init__(self, dependent_vars, expressions):
        self.dependent_variables = dependent_vars
        self.expression = expressions
        super().__init__()
