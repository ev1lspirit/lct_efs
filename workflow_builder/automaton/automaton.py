from functools import partial
import logging
from operator import attrgetter
from typing import TYPE_CHECKING, Optional
from unittest import result
from context import SessionContext
from workflow_builder.automaton.models import StateMetadata
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
        self._workflow_id = workflow_id

        self.zero_state = "__service_Init"
        self.session_context = SessionContext(session_id=session_id)
        self.default_state = self._resolve_initial_state().name
        self.global_state_parser = GlobalStateParser(
            current_state_name=self.default_state, workflow_id=self._workflow_id
        )
        self.states = self._create_states()
        self.state_mapping = {
            state.name: state for state in self.states
        }
        self._current_state = self.state_mapping.get(self.zero_state)

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
        states = self.global_state_parser.get_automaton_subgraph()
        first_state = next(filter(attrgetter("initial_state"), states))
        _zero_state_model = StateModel.zero_state(first_state.name)
        _zero_state = self.build_state(_zero_state_model)
        return [_zero_state] + [self.build_state(state) for state in states]

    @property
    def current_state(self) -> "WorkflowState":
        return self._current_state

    @current_state.setter
    def current_state(self, state: 'WorkflowState'):
        if state is None:
            raise ValueError("No initial state found")
        self._current_state = state

    def _resolve_initial_state(self) -> StateMetadata:
        return self.session_context.get_session_state()

    def _get_transition_candidates_based_on_expressions(self, current_state: 'WorkflowState') -> Optional[Transition]:
        logger.info("Proceeding to next state based on expressions...")
        for expr in current_state.executables:
            result = self.session_context.get(expr.metadata.variable)
            logger.debug(f"Processing expression: {expr}, result: {result}")
            executable_transitions = expr.metadata.transition_bind_object
            for transition in executable_transitions:
                logger.debug(f"Evaluating transition: {transition}")
                if transition.case is None or transition.matches(
                    self.session_context.session
                ):
                    logger.info(f"Transition matched: {transition}")
                    return transition

        for transition in current_state.transitions:
            if transition.case is None:
                return transition
        logger.warning("No matching transition found based on expressions.")
        return None

    def _get_transition_candidates_based_on_event(
        self, current_state: "WorkflowState", event_name: str
    ):
        logger.info(f"Processing event '{event_name}' for screen state...")
        for expr in current_state.executables:
            result = self.session_context.get(expr.metadata.variable)
            logger.info(f"Checking handler for event {expr.metadata.event_name}")
            if result:
                executable_transition = expr.metadata.transition_bind_object
                logger.info(f"Found matching event handler, transition to: {executable_transition.state_id}")
                return executable_transition

    def _evaluate_executables(self, event_name: str = None):
        with self.session_context as context:
            for expression in self.current_state.executables:
                variable = expression.metadata.variable
                try:
                    result = (
                        expression.result(event_name)
                        if self.current_state.type_ == StateTypeEnum.screen
                        else str(expression.result())
                    )
                    context[variable] = result
                except Exception as e:
                    raise RuntimeError(
                        f"Failed to evaluate expression for variable {variable}: {str(e)}"
                    ) from e

    def run(self, event_name: str = None):
        logger.info(f"Beginning pipeline with current state: {self.current_state.type_}")
        while True:
            if self.current_state._final:
                logger.info("Pipeline finished")
                break

            self._evaluate_executables(event_name)

            if self.current_state.type_ == StateTypeEnum.screen:
                # подгрузить экран и отправить экран
                current_state_data = StateMetadata(name=self.current_state.name, type_=self.current_state.type_)
                self.session_context.update_session_state(current_state_data)
                if event_name is None:
                    return
                candidate = self._get_transition_candidates_based_on_event(
                    current_state=self.current_state,
                    event_name=event_name
                )
            else:
                candidate = self._get_transition_candidates_based_on_expressions(
                    current_state=self.current_state
                )

            if candidate is None:
                logger.error(f"No matching transition found: state: {self.current_state.type_}, {self.current_state.name}")
                raise ValueError("No matching transition found")

            next_state_name = candidate.state_id
            logger.info(f"Setting next state: {next_state_name}")
            next_state_object = self.state_mapping.get(next_state_name)
            if next_state_object is None:
                logger.error(f"Next state {next_state_name} not found. Check if it was created.")
                raise ValueError(
                    f"Next state {next_state_name} not found. Check if it was created."
                )
            self.current_state = next_state_object

    def __repr__(self):
        return f"<{self.__class__.__name__} states={self.states}>"
