from collections import deque
from functools import partial

from workflow_builder.expressions import BaseStateExpression, Expression
from typing import TYPE_CHECKING, Dict, Any
import logging
from workflow_builder.models import StateTypeEnum
from .contract import STATE_CLASSES, StateModel
from workflow_builder.transitions import Transition


if TYPE_CHECKING:
    from workflow_builder.states import WorkflowState


logger = logging.getLogger(__name__)


class GlobalStateParser:
    """
    Класс для парсинга входных данных с админ-панели
    """

    def __init__(self, current_state_name: str, data: Dict[str, Any]):
        self.data = data
        self.current_state_name = current_state_name

    def get_automaton_subgraph(self):
        state_mapping = {state.name: state for state in self.parse_states()}
        current_state_mapping = state_mapping.get(self.current_state_name)

        if not current_state_mapping:
            logger.error(f"Current state {self.current_state_name} not found")
            raise ValueError(f"Current state {self.current_state_name} not found")

        queue = deque([current_state_mapping])
        states_to_include = []
        processed = set([current_state_mapping.name])

        while queue:
            state_to_process = queue.popleft()
            states_to_include.append(state_to_process)

            if state_to_process.type_ == StateTypeEnum.screen:
                continue

            for transition in state_to_process.transitions:
                next_state = state_mapping.get(transition.state_id)
                if next_state and next_state.name not in processed:
                    queue.append(next_state)
                    processed.add(next_state.name)

        return states_to_include

    def parse_states(self):
        for raw_state in self.data.get("states", []):
            state = StateModel(**raw_state)  # валидация
            yield self.build_state(state)

    def _parse_entities(self, *, entities, expression_class):
        items = []
        for expression in entities:
            expression_dump = expression.model_dump()
            expression_model = expression_class(**expression_dump)
            items.append(expression_model)
        return items

    def _parse_expressions(self, state: StateModel, expression_class) -> list[BaseStateExpression]:
        expressions = getattr(state, "expressions", [])
        return self._parse_entities(
            entities=expressions, expression_class=expression_class
        )

    # todo: вынести логику в бейс
    def _parse_events(self, state: StateModel, expression_class):
        events = getattr(state, "events", [])
        return self._parse_entities(entities=events, expression_class=expression_class)

    def _parse_transitions(self, state: StateModel):
        transitions = []
        for t in state.transitions:
            if isinstance(t.variable, list):
                for v in t.variable:
                    transitions.append(
                        Transition(variable=v, case=t.case, state_id=t.state_id)
                    )
            else:
                transitions.append(
                    Transition(variable=t.variable, case=t.case, state_id=t.state_id)
                )
        return transitions

    def build_state(self, state: StateModel) -> 'WorkflowState':
        cls = STATE_CLASSES.get(state.state_type)
        if not cls:
            raise ValueError(f"Unsupported state_type: {state.state_type}")

        transitions: list[Transition] = self._parse_transitions(state)
        expression_class = getattr(Expression, state.state_type)

        partialled_cls = partial(
            cls,
            name=state.name,
            transitions=transitions,
            initial_state=state.initial_state,
            final=state.final_state,
        )
        if state.state_type != StateTypeEnum.screen:
            expressions = self._parse_expressions(state, expression_class)
            return partialled_cls(expressions=expressions)
        events = self._parse_events(state, expression_class)
        return partialled_cls(events=events)


"""
Проверка работоспособности
"""
if __name__ == "__main__":
    pass
