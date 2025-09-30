from functools import partial
import logging
from operator import attrgetter
import time
from typing import TYPE_CHECKING, Optional
from context import SessionContext
from utils import call_deadlock_protection
from workflow_builder.automaton.models import StateMetadata
from workflow_builder.expressions import Expression
from workflow_builder.models import StateTypeEnum
from workflow_builder.state_parser.contract import STATE_CLASSES, StateModel
from workflow_builder.state_parser.parser import GlobalStateParser
from workflow_builder.transitions import Transition
from config import settings

if TYPE_CHECKING:
    from ..states import WorkflowState

logger = logging.getLogger(__name__)


class Automaton:

    def __init__(self, *, session_id: str, workflow_id: str):
        self._session_id = session_id
        self._workflow_id = workflow_id

        self.zero_state = settings.SERVICE_INIT_STATE
        self.session_context = SessionContext(
            session_id=session_id, workflow_id=self._workflow_id
        )
        self.initial_state_name = self._resolve_initial_state().name
        self.global_state_parser = GlobalStateParser(
            current_state_name=self.initial_state_name, workflow_id=self._workflow_id
        )
        self.states = self._create_states()
        self.state_mapping = {state.name: state for state in self.states}
        self._current_state = self.state_mapping.get(self.zero_state)
        self._actual_current_state = self.state_mapping[self.initial_state_name]

    def build_state(self, state: StateModel) -> "WorkflowState":
        cls = STATE_CLASSES.get(state.state_type)
        if not cls:
            raise ValueError(f"Unsupported state_type: {state.state_type}")

        transitions: list[Transition] = self.global_state_parser._parse_transitions(
            state
        )
        expression_class = getattr(Expression, state.state_type)

        partialled_cls = partial(
            cls,
            name=state.name,
            context=self.session_context,
            transitions=transitions,
            initial_state=state.initial_state,
            final=state.final_state,
        )
        if state.state_type == StateTypeEnum.service:
            expressions = [
                Expression.service(
                    mongo_collection_name=settings.WORKFLOW_MONGO_COLLECTION
                )
            ]
        else:
            expressions = self.global_state_parser._parse_expressions(
                    state, expression_class
            )

        return partialled_cls(expressions=expressions)

    def _create_states(self):
        if self.initial_state_name == settings.SERVICE_INIT_STATE:
            next_state = next(
                filter(attrgetter("initial_state"), self.global_state_parser.data), None
            )
            if next_state is None:
                logger.error(
                    f"No initial state found! WF: {self._workflow_id}, Session: {self._session_id}"
                )
                raise ValueError("No initial state found")
            next_state_name = next_state.name
        else:
            next_state_name = self.initial_state_name
        _error_state_model = StateModel.error_state()
        _zero_state_model = StateModel.zero_state(next_state_name)
        self.global_state_parser.data = [_zero_state_model
        ] + self.global_state_parser.data + [_error_state_model]
        states = self.global_state_parser.get_automaton_subgraph()
        return [self.build_state(state) for state in states]

    @property
    def current_state(self) -> "WorkflowState":
        return self._current_state

    @current_state.setter
    def current_state(self, state: "WorkflowState"):
        if state is None:
            raise ValueError("No initial state found")
        self._current_state = state

    def _resolve_initial_state(self) -> StateMetadata:
        return self.session_context.get_session_state()

    def _get_transition_candidates_based_on_expressions(
        self, current_state: "WorkflowState"
    ) -> Optional[Transition]:
        logger.info("Proceeding to next state based on expressions...")
        for expr in current_state.executables:
            if not expr.metadata.bindable():
                continue
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
            result = expr.result(event_name)
            logger.info(f"Checking handler for event {expr.metadata.event_name}")
            if result:
                executable_transition = expr.metadata.transition_bind_object
                logger.info(
                    f"Found matching event handler, transition to: {executable_transition.state_id}"
                )
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

    def _evaluate_service_executables(self):
        for expression in self.current_state.executables:
            try:
                expression.result()
            except Exception as e:
                raise RuntimeError(f"Failed to evaluate expression: {str(e)}")

    def _call_state_checkpoint(self) -> None:
        try:
            current_state_data = StateMetadata(
                name=self.current_state.name, type_=self.current_state.type_
            )
            self.session_context.update_session_state(current_state_data)
        except Exception as e:
            logger.error(f"Failed to update session state. Error: {e}")
            raise e

    def _get_on_return_policy(self):
        on_return = True
        if self._actual_current_state.type_ == StateTypeEnum.screen:
            on_return = False
        return on_return

    def run(self, event_name: str = None):
        logger.info(
            f"Beginning pipeline with current state: {self.current_state.type_}"
        )
        start_time = time.time()
        on_return = self._get_on_return_policy()

        while True:
            if self.current_state._final:
                logger.info("Pipeline finished")
                break

            if self.current_state.type_ == StateTypeEnum.screen:
                if on_return:
                    # returns screen data
                    self._call_state_checkpoint()
                    return
                candidate = self._get_transition_candidates_based_on_event(
                    current_state=self.current_state, event_name=event_name
                )
            else:
                # call_deadlock_protection(start_time)
                evaluator = (
                    self._evaluate_service_executables
                    if self.current_state.type_ == StateTypeEnum.service
                    else partial(self._evaluate_executables, event_name)
                )
                evaluator()
                candidate = self._get_transition_candidates_based_on_expressions(
                    current_state=self.current_state
                )
            if candidate is None:
                logger.error(
                    f"No matching transition found: state: {self.current_state.type_}, {self.current_state.name}"
                )
                raise ValueError("No matching transition found")

            next_state_name = candidate.state_id
            logger.info(f"Setting next state: {next_state_name}")
            next_state_object = self.state_mapping.get(next_state_name)
            if next_state_object is None:
                logger.error(
                    f"Next state {next_state_name} not found. Check if it was created."
                )
                raise ValueError(
                    f"Next state {next_state_name} not found. Check if it was created."
                )
            self.current_state = next_state_object

    def __repr__(self):
        return f"<{self.__class__.__name__} states={self.states}>"
