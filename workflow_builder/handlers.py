from dataclasses import dataclass
from attr import define
from functools import cached_property
from typing import Any, TypeVar
from uuid import UUID


HandlerClass = TypeVar("HandlerClass")


@dataclass
class HandlerMeta:
    variable: str  # variable to be updated
    dependent_variables: list[str]  # a list of dependent variables
    execution_context: str  # python execution lambda


@define
class TechnicalHandler:
    state_uid: UUID
    metadata: HandlerMeta
    context: dict[str, Any]

    @cached_property
    def result(self):
        res = eval(self.metadata.execution_context, locals=self.context)
        self.context.update({self.metadata.variable: res})
