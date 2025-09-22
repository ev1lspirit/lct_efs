from abc import ABC, abstractmethod
from attr import define, field
from typing import Any, TypeVar


HandlerClass = TypeVar("HandlerClass")


@define
class TechnicalStateAction:
    variable: str  # variable to be updated
    dependent_variables: list[str]  # a list of dependent variables
    expression: str  # python execution lambda


@define
class IntegrationStateAction:
    variable: str = field()  # variable to be updated
    url: str = field()  # endpoint URL
    params: dict[str, Any] = field()  # query or body params
    method: str = field(default="get") # GET, POST, etc.


class BaseHandler(ABC):
    metadata: Any
    context: dict[str, Any]

    @abstractmethod
    def result(self):
        raise NotImplementedError


@define
class TechnicalHandler:
    metadata: TechnicalStateAction
    context: dict[str, Any]

    def result(self):
        return {
            self.metadata.variable: eval(self.metadata.expression, locals=self.context)
        }


@define
class IntegrationHandler:
    adapter: Any  # CommonAdapter  # type: ignore[name-defined]
    metadata: IntegrationStateAction
    context: dict[str, Any]

    def result(self):
        adapter = self.adapter(url=self.metadata.url)
        response = adapter.request(method=self.metadata.method, params=self.metadata.params)
        return {self.metadata.variable: response}
