import logging
from operator import attrgetter
from typing import TYPE_CHECKING, Optional
from pydantic import BaseModel

from workflow_builder.models import StateTypeEnum

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

    def _get_transition_candidates_based_on_expressions(self):
        logger.info("Proceeding to next state based on expressions...")
        candidates = []
        for expr in self.current_state.executables:
            logger.info(f"Executing expression {expr.metadata.expression} of class {expr.__class__.__name__}")
            result = expr.result()
            executable_transition = expr.metadata.transition_bind_object
            executable_case = eval(executable_transition.case)
            logger.info(f"Case: {executable_case}, Result: {result}")
            if result == executable_case:
                candidates.append(executable_transition)

        return candidates

    def _get_transition_candidates_based_on_event(self, event_name: str):
        pass

    def run(self):
        logger.info(f"Beginning pipeline with current state: {self.current_state.type_}")
        while True:
            if self.current_state._final:
                logger.info("Pipeline finished")
                break
            if self.current_state.type_ == StateTypeEnum.screen:
                event_name = yield
                candidates = self._get_transition_candidates_based_on_event(event_name)
            else:
                candidates = self._get_transition_candidates_based_on_expressions()

            if len(candidates) > 1:
                logger.error(f"Multiple candidates found. Resolve ambiguity and pick one. Candidates: {candidates}")
                break
            elif len(candidates) == 0:
                logger.error("No candidates found. Transition is impossible.")
                break
            else:
                next_state_name = candidates[0].state_id
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
