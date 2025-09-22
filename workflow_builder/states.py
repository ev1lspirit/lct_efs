from __future__ import annotations
from abc import ABC
from functools import partial
from typing import Callable, ClassVar
import uuid

from context import SessionContext
from workflow_builder.handlers import HandlerMeta

context = SessionContext({"z": 1, "y": 7, "l": 4, "x": None})
from .models import StateTypeEnum, state_mapping


class WorkflowState(ABC):
    type_: ClassVar[StateTypeEnum]
    context: ClassVar[SessionContext] = SessionContext()

    def __init__(self, transitions: list, handlers: list[HandlerMeta]):
        self.uid = uuid.uuid4()
        self.state_local_context = {}
        self.handlers: list[HandlerMeta] = handlers
        self.transitions = transitions
        self.executables = {}
        self.adapters = {}

    def _resolve_exec_creator(self):
        handlers_creator = state_mapping.get(self.type_)
        if handlers_creator is None:
            # raise ValueError(f"Unsupported state type: {self.type_}")
            return lambda: {}
        return handlers_creator(workflow_state=self, handlers=self.handlers)

    def execute(self):
        for executable in self.executables.get(self.uid, []):
            self.state_local_context.update(executable.result())
        return self.state_local_context

    def _resolve_adapter(self) -> Callable[[], list]:
        return lambda: []

    def __repr__(self):
        return f"<{self.__class__.__name__} uid={self.uid} type={self.type_}>"


class TechnicalState(WorkflowState):
    type_ = StateTypeEnum.technical

    def __init__(self, transitions: list, handlers: list[HandlerMeta]):
        super().__init__(transitions, handlers)
        self.executables = self._resolve_exec_creator()()
        self.adapters = self._resolve_adapter()()


class ScreenState(WorkflowState):
    type_ = StateTypeEnum.screen


class IntegrationState(WorkflowState):
    type_ = StateTypeEnum.integration


if __name__ == "__main__":
    obj = TechnicalState(
        transitions=[],
        handlers=[HandlerMeta(
            variable="x",
            dependent_variables=["z", "y"],
            expression="z*2-y",
        )],
    )
    print(SessionContext())
    SessionContext().update({"z": 100})
    local_context = obj.execute()
    SessionContext().update(local_context)
