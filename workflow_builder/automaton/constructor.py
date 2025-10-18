import logging
from config import settings
from context import SessionContext
from workflow_builder.expressions import Expression
from workflow_builder.models import StateTypeEnum
from workflow_builder.state_parser.contract import STATE_CLASSES, StateModel
from workflow_builder.state_parser.parser import GlobalStateParser
from workflow_builder.states import WorkflowState
from workflow_builder.transitions import Transition

from attrs import define, field

from functools import partial
from operator import attrgetter


logger = logging.getLogger(__name__)


@define
class StateConstructor:
    session_context: SessionContext = field()
    initial_state_name: str = field()
    workflow_id: str = field()
    session_id: str = field()
    global_state_parser: GlobalStateParser = field(init=False)

    def __attrs_post_init__(self):
        self.global_state_parser = GlobalStateParser(
            current_state_name=self.initial_state_name, workflow_id=self.workflow_id
        )

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

    def create_states(self):
        if self.initial_state_name == settings.SERVICE_INIT_STATE:
            next_state = next(
                filter(attrgetter("initial_state"), self.global_state_parser.data), None
            )
            if next_state is None:
                logger.error(
                    f"No initial state found! WF: {self.workflow_id}, Session: {self.session_id}"
                )
                raise ValueError("No initial state found")
            next_state_name = next_state.name
        else:
            next_state_name = self.initial_state_name
        _error_state_model = StateModel.error_state()
        _zero_state_model = StateModel.zero_state(next_state_name)
        self.global_state_parser.data = (
            [_zero_state_model] + self.global_state_parser.data + [_error_state_model]
        )
        states = self.global_state_parser.get_automaton_subgraph()
        return [self.build_state(state) for state in states]
