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

    def _parse_expressions(self, state: StateModel, expression_class) -> list[BaseStateExpression]:
        expressions = []
        for expression in state.expressions:
            expression_dump = expression.model_dump()
            transition_bind = expression_dump.pop("transition_bind", None)
            expression_model = expression_class(**expression_dump)
            if transition_bind is not None:
                expression_model = expression_model.bind_transition(name=transition_bind)
                expressions.append(expression_model)
        return expressions

    # todo: вынести логику в бейс
    def _parse_events(self, state: StateModel, expression_class):
        events = []
        for event in state.events:
            event_dump = event.model_dump()
            transition_bind = event_dump.pop("transition_bind", None)
            event_model = expression_class(**event_dump)
            if transition_bind is not None:
                event_model = event_model.bind_transition(name=transition_bind)
                events.append(event_model)
        return events

    def build_state(self, state: StateModel) -> 'WorkflowState':
        cls = STATE_CLASSES.get(state.state_type)
        if not cls:
            raise ValueError(f"Unsupported state_type: {state.state_type}")
        transitions = [Transition(case=t.case, state_id=t.state_id) for t in state.transitions]
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
    test_json  = {
        "states": [
            {
                "state_type": "technical",
                "name": "Init",
                "transitions": [
                    {"case": "success", "state_id": "LoadData"},
                    {"case": "error", "state_id": "ErrorState"},
                ],
                "expressions": [
                    {
                        "transition_bind": "LoadData",
                        "variable": "data_loaded",
                        "dependent_variables": [],
                        "expression": "lambda: True",
                    }
                ],
                "initial_state": True,
                "final_state": False,
            },
            {
                "state_type": "integration",
                "name": "LoadData",
                "transitions": [
                    {"case": "loaded", "state_id": "ProcessData"},
                    {"case": "missing", "state_id": "ErrorState"},
                ],
                "expressions": [
                    {
                        "transition_bind": "ProcessData",
                        "variable": "records",
                        "url": "https://api.example.com/data",
                        "params": {"limit": 100},
                        "method": "get",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "ProcessData",
                "transitions": [
                    {"case": "processed", "state_id": "ShowScreen"},
                    {"case": "fail", "state_id": "ErrorState"},
                ],
                "expressions": [
                    {
                        "transition_bind": "ShowScreen",
                        "variable": "processed",
                        "dependent_variables": ["records"],
                        "expression": "lambda records: records > 0",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "ShowScreen",
                "transitions": [{"case": "continue", "state_id": "Final"}],
                "expressions": [
                    {
                        "transition_bind": "Final",
                        "event_name": "render_ui",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "Final",
                "transitions": [],
                "expressions": [],
                "initial_state": False,
                "final_state": True,
            },
            {
                "state_type": "technical",
                "name": "ErrorState",
                "transitions": [],
                "initial_state": False,
                "final_state": True,
            },
        ]
    }

    parser = GlobalStateParser(current_state_name="Init", data=test_json)
    states = parser.get_automaton_subgraph()
