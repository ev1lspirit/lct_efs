from dataclasses import dataclass
from attr import define
from typing import Any, TypeVar
from uuid import UUID


HandlerClass = TypeVar("HandlerClass")


@dataclass
class HandlerMeta:
    variable: str  # variable to be updated
    dependent_variables: list[str]  # a list of dependent variables
    expression: str  # python execution lambda


@define
class TechnicalHandler:
    state_uid: UUID
    metadata: HandlerMeta
    context: dict[str, Any]

    def result(self):
        return {
            self.metadata.variable: eval(self.metadata.expression, locals=self.context)
        }
