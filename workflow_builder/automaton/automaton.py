from functools import partial
import logging
from operator import attrgetter
from typing import TYPE_CHECKING, Optional
from pydantic import BaseModel

from context import SessionContext
from storage.redis.service import get_redis_cache
from workflow_builder.expressions import Expression
from workflow_builder.models import StateTypeEnum
from workflow_builder.state_parser.contract import STATE_CLASSES, StateModel
from workflow_builder.state_parser.parser import GlobalStateParser
from workflow_builder.transitions import Transition

if TYPE_CHECKING:
    from ..states import WorkflowState

logger = logging.getLogger(__name__)

class Automaton:

    def __init__(self, *, session_id: str, workflow_id: str):
        self._session_id = session_id
        self.session_context = SessionContext(session_id=session_id)
        self._workflow_id = workflow_id
        self.global_state_parser = GlobalStateParser(current_state_name="Init", workflow_id=self._workflow_id)
        self.states = self._create_states()
        self.state_mapping = {
            state.name: state for state in self.states
        }
        self._current_state: 'WorkflowState' = self._resolve_initial_state() # type: ignore

    def build_state(self, state: StateModel) -> "WorkflowState":
        cls = STATE_CLASSES.get(state.state_type)
        if not cls:
            raise ValueError(f"Unsupported state_type: {state.state_type}")

        transitions: list[Transition] = self.global_state_parser._parse_transitions(state)
        expression_class = getattr(Expression, state.state_type)

        partialled_cls = partial(
            cls,
            name=state.name,
            context=self.session_context,
            transitions=transitions,
            initial_state=state.initial_state,
            final=state.final_state,
        )
        if state.state_type != StateTypeEnum.screen:
            expressions = self.global_state_parser._parse_expressions(state, expression_class)
            return partialled_cls(expressions=expressions)
        events = self.global_state_parser._parse_events(state, expression_class)
        return partialled_cls(events=events)

    def _create_states(self):
        return [self.build_state(state) for state in self.global_state_parser.get_automaton_subgraph()]

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
            logger.debug(f"Processing expression: {expr}, result: {result}")
            executable_transitions = expr.metadata.transition_bind_object
            context[expr.metadata.variable] = result
            logger.debug(f"Updated context: {context}")
            for transition in executable_transitions:
                logger.debug(f"Evaluating transition: {transition}")
                if transition.case is None or transition.matches(context):
                    logger.info(f"Transition matched: {transition}")
                    return transition
        logger.warning("No matching transition found based on expressions.")
        return None

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

            expression_results = {
                exp.metadata.variable: exp.result(event_name) if self.current_state.type_ == StateTypeEnum.screen
                else str(exp.result())
                for exp in self.current_state.executables
            }

            if self.current_state.type_ == StateTypeEnum.screen:
                # подгрузить экран и отправить экран
                candidate = self._get_transition_candidates_based_on_event(
                    zip(self.current_state.executables, expression_results.values()), event_name=event_name
                )
            else:
                candidate = self._get_transition_candidates_based_on_expressions(
                    zip(self.current_state.executables, expression_results.values())
                )

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

    def __repr__(self):
        return f"<{self.__class__.__name__} states={self.states}>"
