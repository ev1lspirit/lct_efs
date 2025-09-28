import logging
from operator import attrgetter
from typing import TYPE_CHECKING, Optional
from pydantic import BaseModel

from workflow_builder.models import StateTypeEnum
from workflow_builder.transitions import Transition

if TYPE_CHECKING:
    from ..states import WorkflowState

logger = logging.getLogger(__name__)

class Automaton:

    def __init__(self, states: list['WorkflowState']):
        self.states = states
        self.state_mapping = {
            state.name: state for state in self.states
        }
        self._current_state: 'WorkflowState' = self._resolve_initial_state() # type: ignore

    @property
    def current_state(self):
        return self._current_state

    @current_state.setter
    def current_state(self, state: 'WorkflowState'):
        if state is None:
            raise ValueError("No initial state found")
        self._current_state = state

    def _resolve_initial_state(self) -> Optional['WorkflowState']:
        return next(
            iter(
                filter(attrgetter('initial_state'), self.states)
            ), None
        )

    def _get_transition_candidates_based_on_expressions(self, expressions_and_results) -> Optional[Transition]:
        logger.info("Proceeding to next state based on expressions...")
        context = {}
        for expr, result in expressions_and_results:
            executable_transitions = expr.metadata.transition_bind_object
            context[expr.metadata.variable] = result
            for transition in executable_transitions:
                if transition.matches(context):
                    return transition

    def _get_transition_candidates_based_on_event(
        self, expressions_and_results, event_name: str
    ):
        logger.info(f"Processing event '{event_name}' for screen state...")
        for handler, result in expressions_and_results:
            logger.info(f"Checking handler for event {handler.metadata.event_name}")
            if result:
                executable_transition = handler.metadata.transition_bind_object
                logger.info(f"Found matching event handler, transition to: {executable_transition.state_id}")
                return executable_transition

    def run(self, event_name: str = None):
        logger.info(f"Beginning pipeline with current state: {self.current_state.type_}")
        while True:
            if self.current_state._final:
                logger.info("Pipeline finished")
                break

            if event_name:
                # Отправляем экран на фронт
                # screen_data = self.current_state.send_to_front()
                # logger.info(f"Sending screen to front: {screen_data.get('name', 'unknown')}")
                expression_results = [
                    exp.result(event_name) for exp in self.current_state.executables
                ]
                candidate = self._get_transition_candidates_based_on_event(
                    zip(self.current_state.executables, expression_results), event_name=event_name
                )
            else:
                expression_results = [
                    str(exp.result()) for exp in self.current_state.executables
                ]
                candidate = self._get_transition_candidates_based_on_expressions(zip(
                    self.current_state.executables, expression_results))

            if candidate is None:
                logger.error(f"No matching transition found: state: {self.current_state.type_}, {self.current_state.name}")
                raise ValueError("No matching transition found")

            next_state_name = candidate.state_id
            next_state_object = self.state_mapping.get(next_state_name)
            if next_state_object is None:
                logger.error(f"Next state {next_state_name} not found. Check if it was created.")
                raise ValueError(
                    f"Next state {next_state_name} not found. Check if it was created."
                )
            self.current_state = next_state_object

    @classmethod
    def from_workflow_description(cls, workflow_description: BaseModel):
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__} states={self.states}>"
