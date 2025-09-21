from __future__ import annotations
from abc import ABC, abstractmethod
from pyclbr import Class
from typing import Any, ClassVar
import uuid
from uuid import UUID

from context import SessionContext
from .models import StateTypeEnum, state_mapping


class StateContext:

    def __init__(self, state: WorkflowState, *args, **kwargs):
        self.state= state
        self.handler_creator = self.resolve_handler_creator()
        self.handler_adapter = self.resolve_adapter()

    def resolve_handler_creator(self):
        return state_mapping.get(self.state.type_)

    def resolve_adapter(self):
        pass

class WorkflowState(ABC):
    type_: ClassVar[StateTypeEnum]
    context: ClassVar[SessionContext] = SessionContext()

    def __init__(self):
        self.state_local_context: StateContext = StateContext(self)

    @abstractmethod
    def get_handlers(self) -> Any:
        ...


class TechnicalState(WorkflowState):
    type_ = StateTypeEnum.technical

    def get_handlers(self):
        # todo: придумать как передавать handlers meta
        return self.state_local_context.handler_creator(self, self.context)


class ScreenState(WorkflowState):
    type_ = StateTypeEnum.screen


class IntegrationState(WorkflowState):
    type_ = StateTypeEnum.integration


if __name__ == "__main__":
    obj = TechnicalState()
    print(obj.context)
    if obj.context is not None:
        obj.context.handler_creator() #type: ignore # класс WorkflowTechnicalHandlersCreator
