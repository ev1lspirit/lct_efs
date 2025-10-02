from collections import deque
from functools import reduce
import operator

from workflow_builder.expressions import BaseStateExpression, Expression
from typing import TYPE_CHECKING
import logging
from workflow_builder.models import StateTypeEnum
from .workflow_cache import workflow_cache
from .contract import StateModel
from workflow_builder.transitions import Transition
from config import settings


logger = logging.getLogger(__name__)


class GlobalStateParser:
    """
    Класс для парсинга входных данных с админ-панели
    """

    def __init__(self, current_state_name: str, workflow_id: str):
        self.data = []
        self.workflow_id = workflow_id
        self.current_state_name = current_state_name
        if not self.data:
            self.data = self._load_workflow()

    def get_automaton_subgraph(self):
        state_mapping = {state.name: state for state in self.data}
        current_state_mapping = state_mapping.get(self.current_state_name)
        if not current_state_mapping:
            logger.error(f"Current state {self.current_state_name} not found")
            raise ValueError(f"Current state {self.current_state_name} not found")

        on_continue = True
        if current_state_mapping.state_type == StateTypeEnum.screen:
            on_continue = False

        current_state_mapping = state_mapping.get(settings.SERVICE_INIT_STATE)
        queue = deque([current_state_mapping])
        states_to_include = []
        processed = set([current_state_mapping.name])

        while queue:
            state_to_process = queue.popleft()
            states_to_include.append(state_to_process)

            if state_to_process.state_type == StateTypeEnum.screen:
                if on_continue:
                    on_continue = not on_continue
                    continue

            for transition in state_to_process.transitions:
                next_state = state_mapping.get(transition.state_id)
                if next_state and next_state.name not in processed:
                    queue.append(next_state)
                    processed.add(next_state.name)
        return states_to_include

    def _load_workflow(self) -> list[StateModel]:
        """Load workflow from cache/MongoDB with detailed error reporting"""
        logger.debug(f"Loading workflow {self.workflow_id} for state {self.current_state_name}")
        states: list[StateModel] = workflow_cache.get_workflow(self.workflow_id)
        if not states:
            error_msg = (
                f"Workflow {self.workflow_id} not found in MongoDB.\n"
                f"Possible causes:\n"
                f"1. Workflow ID is incorrect or doesn't exist\n"
                f"2. Workflow was not saved using POST /workflow/save endpoint\n"
                f"3. MongoDB connection issues\n"
                f"4. Workflow was saved to different database/collection\n\n"
                f"Check MongoDB collection: states (database: test)"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        logger.info(f"Loaded {len(states)} states for workflow {self.workflow_id}")
        return states

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

    def _parse_events(self, state: StateModel, expression_class):
        events = getattr(state, "events", [])
        return self._parse_entities(entities=events, expression_class=expression_class)

    def _parse_transitions(self, state: StateModel):
        transitions = []
        for t in state.transitions:
            if isinstance(t.variable, list):
                trabsition_models = [Transition(
                    variable=var, case=t.case, state_id=t.state_id
                ) for var in t.variable]
                transition = reduce(operator.and_, trabsition_models)
            else:
                transition = Transition(variable=t.variable, case=t.case, state_id=t.state_id)
            transitions.append(transition)
        return transitions
