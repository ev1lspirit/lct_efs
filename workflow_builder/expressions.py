from functools import wraps
from attr import define, field, validators
from typing import Any, ClassVar, Optional

from storage.mongo.client import MongoDBClient
from storage.redis.service import RedisCache
from workflow_builder.models import StateTypeEnum
from workflow_builder.transitions import Transition
import logging
from config import settings


logger = logging.getLogger(__name__)


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

    _transition_bind_object: Any = field(default=None, init=False)
    type_: ClassVar[StateTypeEnum]

    @property
    def transition_bind_object(self) -> Transition:
        return self._transition_bind_object

    @transition_bind_object.setter
    def transition_bind_object(self, transition: Transition):
        if transition is not None:
            if not isinstance(transition, list):
                raise ValueError(
                    f"Expected list[Transition], got {type(transition).__name__}"
                )
        self._transition_bind_object = transition

    def bindable(self):
        return True

    # def bind_transition(self, name: str):
    #     if self.transition_bind is not None:
    #         raise ValueError("Transition already bound")
    #     self._transition_bind = name
    #     return self


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

    # __slots__ = ["dependent_variables"]

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

    variable: str = field(
        validator=validators.instance_of(str)
    )  # variable to be updated
    dependent_variables: list[str] = field(
        validator=validators.instance_of(list)
    )  # a list of dependent variables
    expression: str = field(
        validator=validators.instance_of(str)
    )  # python execution lambda
    type_: ClassVar[StateTypeEnum] = StateTypeEnum.technical


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

    event_name: str = field(validator=validators.instance_of(str))
    type_: ClassVar[StateTypeEnum] = StateTypeEnum.screen


@define(slots=True)
class ServiceStateExpression(BaseStateExpression):
    redis_client: RedisCache = field(validator=validators.instance_of(RedisCache))
    mongo_client: MongoDBClient = field(validator=validators.instance_of(MongoDBClient))
    type_: ClassVar[StateTypeEnum] = StateTypeEnum.service

    def bindable(self):
        return False


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
        dependent_variables (list[str]): список переменных из context, требуемых в params (опционально)
        error_variable (Optional[str]): переменная для сохранения ошибки API (опционально)

    Methods:
        execute (SessionContext, **kwargs): execute expression (must be overridden by subclasses)

    Examples:
        >>> from workflow_builder.expressions import Expression
        >>> expr = Expression.integration(
        ...     variable="user_data",
        ...     url="http://api.example.com/users",
        ...     params={"user_id": "{{user_id}}"},
        ...     dependent_variables=["user_id"]
        ... )
        >>> expr.variable
        'user_data'
        >>> expr.url
        'http://api.example.com/users'
        >>> expr.params
        {'user_id': '{{user_id}}'}
        >>> expr.dependent_variables
        ['user_id']

    Notes:
        IntegrationStateExpression is a subclass of BaseStateExpression
        dependent_variables - автоматически проверяется декоратором @check_context_consistency
        error_variable - позволяет сохранить APIError в контекст для обработки в transitions
    """

    variable: str = field(validator=validators.instance_of(str))
    url: str = field(validator=validators.instance_of(str))  # endpoint URL
    params: Optional[dict[str, Any]] = field(
        default=None, validator=validators.optional(validators.instance_of(dict))
    )  # query params для GET/DELETE
    body: Optional[dict[str, Any]] = field(
        default=None, validator=validators.optional(validators.instance_of(dict))
    )  # body params для POST/PUT/PATCH
    method: str = field(
        default="get",
        validator=validators.in_(["get", "post", "put", "delete", "patch"]),
    )  # HTTP method
    dependent_variables: list[str] = field(
        factory=list, validator=validators.instance_of(list)
    )  # переменные из context, необходимые для params/body
    error_variable: Optional[str] = field(
        default=None, validator=validators.optional(validators.instance_of(str))
    )  # переменная для сохранения ошибки
    type_: ClassVar[StateTypeEnum] = StateTypeEnum.integration


class Expression:
    """Helper class to create state expressions"""

    @classmethod
    def technical(
        cls, *, variable: str, dependent_variables: list[str], expression: str
    ) -> "TechnicalStateExpression":
        return TechnicalStateExpression(
            variable=variable,
            dependent_variables=dependent_variables,
            expression=expression,
        )

    @classmethod
    def integration(
        cls,
        *,
        variable: str,
        url: str,
        params: dict[str, Any] = None,
        body: dict[str, Any] = None,
        method: str = "get",
        dependent_variables: list[str] = None,
        error_variable: str = None
    ) -> "IntegrationStateExpression":
        return IntegrationStateExpression(
            variable=variable,
            url=url,
            params=params,
            body=body,
            method=method,
            dependent_variables=dependent_variables or [],
            error_variable=error_variable
        )

    @classmethod
    def screen(cls, *, event_name: str):
        return ScreenStateExpression(event_name=event_name)

    @classmethod
    def service(cls, mongo_collection_name):
        return ServiceStateExpression(
            redis_client=RedisCache(),
            mongo_client=MongoDBClient(
                database=settings.MONGO_DB, collection=mongo_collection_name
            ),
        )


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
