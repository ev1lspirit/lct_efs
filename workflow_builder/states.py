from __future__ import annotations

from context import SessionContext
from .automaton.automaton import Automaton

context = SessionContext({"z": 1, "y": 7, "l": 4, "balance": 100, "x": 100})
from abc import ABC
from typing import ClassVar
import uuid
from .expressions import Expression
from workflow_builder.transitions import Transition
from .models import StateTypeEnum, state_mapping


class WorkflowState(ABC):
    """Базовое состояние"""

    type_: ClassVar[StateTypeEnum]
    context: ClassVar[SessionContext] = SessionContext()

    def __init__(
        self,
        context_variable: str,
        transitions: list[Transition],
        expressions: list,
        initial_state: bool = False,
    ):
        self.uid = uuid.uuid4()
        self.initial_state = initial_state
        self.context_variable = context_variable
        self.state_local_context = {}
        self.expressions: list = expressions
        self.transitions = transitions
        self.executables = self._create_exec_handlers()

    @property
    def transition_map(self) -> dict[str, Transition]:
        return {t.state_id: t for t in self.transitions}

    def _create_exec_handlers(self, **kwargs):
        creator = self._resolve_exec_creator()
        return creator(**kwargs)

    def _resolve_exec_creator(self):
        handlers_creator = state_mapping.get(self.type_)
        if handlers_creator is None:
            return lambda: {}
        return handlers_creator(workflow_state=self, handlers=self.expressions)

    def _bind_transtions_and_expressions(self):
        bind_map = self.transition_map
        for expr in self.expressions:
            transition = bind_map.get(expr.transition_bind)
            if transition is None:
                raise ValueError(f"Transition with id={expr.transition_bind} not found")
            expr.transition_bind_object = transition

    def __repr__(self):
        return f"<{self.__class__.__name__} uid={self.uid} type={self.type_}>"


class TechnicalState(WorkflowState):
    type_ = StateTypeEnum.technical

    def __init__(
        self,
        context_variable: str,
        transitions: list[Transition],
        expressions: list,
        initial_state: bool = False,
    ):
        super().__init__(context_variable, transitions, expressions, initial_state)
        self._bind_transtions_and_expressions()


class IntegrationState(WorkflowState):
    type_ = StateTypeEnum.integration

    def __init__(
        self,
        context_variable: str,
        transitions: list[Transition],
        expressions: list,
        initial_state: bool = False,
    ):
        super().__init__(context_variable, transitions, expressions, initial_state)
        self._bind_transtions_and_expressions()


class ScreenState(WorkflowState):
    type_ = StateTypeEnum.screen


if __name__ == "__main__":
    obj = TechnicalState(
        initial_state=True,
        context_variable="x",
        transitions=[
            Transition(case="True", state_id="next_id"),
            Transition(case="False", state_id="prev_id"),
        ],
        expressions=[
            (
                Expression.technical(
                    dependent_variables=["balance"], expression="balance>0"
                )
                & Expression.technical(dependent_variables=["x"], expression="x>0")
            ).bind_transition(name="next_id")
        ],
    )
    # integration = IntegrationState(
    #     context_variable="z",
    #     transitions=[
    #         Transition(case="True", state_id="next_id")
    #     ],
    #     expressions=[
    #         Expression.integration(
    #             variable="z",
    #             url="http://example.com",
    #             params={"param": "value"},
    #         ).bind_transition(name="next_id")
    #     ]
    # )
    automaton = Automaton(states=[obj])
    for state in automaton:
        print(state)
