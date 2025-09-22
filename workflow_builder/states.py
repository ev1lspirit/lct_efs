from __future__ import annotations
from abc import ABC
from typing import ClassVar
import uuid
from context import SessionContext
from workflow_builder.handlers import IntegrationStateAction, TechnicalStateAction

context = SessionContext({"z": 1, "y": 7, "l": 4, "x": None})
from .models import StateTypeEnum, state_mapping


class WorkflowState(ABC):
    type_: ClassVar[StateTypeEnum]
    context: ClassVar[SessionContext] = SessionContext()

    def __init__(self, transitions: list, handler_params: list):
        self.uid = uuid.uuid4()
        self.state_local_context = {}
        self.handler_params: list = handler_params
        self.transitions = transitions
        exec_creator = self._resolve_exec_creator()
        self.executables = exec_creator()

    def _resolve_exec_creator(self):
        handlers_creator = state_mapping.get(self.type_)
        if handlers_creator is None:
            # raise ValueError(f"Unsupported state type: {self.type_}")
            return lambda: {}
        return handlers_creator(workflow_state=self, handlers=self.handler_params)

    def execute(self):
        for executable in self.executables:
            self.state_local_context.update(executable.result())
        return self.state_local_context

    def __repr__(self):
        return f"<{self.__class__.__name__} uid={self.uid} type={self.type_}>"


class TechnicalState(WorkflowState):
    type_ = StateTypeEnum.technical


class ScreenState(WorkflowState):
    type_ = StateTypeEnum.screen


class IntegrationState(WorkflowState):
    type_ = StateTypeEnum.integration


if __name__ == "__main__":
    obj = TechnicalState(
        transitions=[],
        handler_params=[
            TechnicalStateAction(
                variable="x",
                dependent_variables=["z", "y"],
                expression="z*2-y",
            )
        ],
    )
    integration = IntegrationState(
        transitions=[],
        handler_params=[
            IntegrationStateAction(
                variable="z",
                url="http://example.com",
                params={"param": "value"},
            )
        ]
    )
    print(SessionContext())
    SessionContext().update({"z": 100})
    local_context = obj.execute()
    int_context = integration.execute()
    SessionContext().update(local_context)
