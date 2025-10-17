from utils import AmbiguityFreeList
from validators.mixins import AssertCallerMixin
from .state import (
    IntegrationStateValidator,
    ScreenStateValidator,
    StateValidator,
    TechnicalStateValidator,
)
from workflow_builder.models import StateTypeEnum
from workflow_builder.state_parser.contract import StateModel
from attr import define, field, validators as v
from collections import defaultdict
from operator import attrgetter
from typing import Callable, Type
from venv import logger


@define
class AutomatonValidator:
    states: list[StateModel] = field(validator=v.instance_of(list))
    automaton_context: dict = field(default={}, init=False)

    def __attrs_post_init__(self) -> None:
        self.automaton_context = defaultdict(AmbiguityFreeList)
        self._assert_final_state()
        self._assert_initial_state()

    def _assert_type(self, state: StateModel) -> StateTypeEnum:
        type_ = StateTypeEnum(state.state_type)
        if type_ is None:
            raise ValueError(
                f"Unknown state type: {type_}. Expected one of {list(StateTypeEnum)}"
            )
        return type_

    def _assert_initial_state(self):
        initial = None
        for state in self.states:
            if state.initial_state:
                if initial is not None:
                    raise ValueError(
                        "Only one initial state is allowed. First: {}, Second: {}".format(
                            initial, state
                        )
                    )
                initial = state
        if initial is None:
            raise ValueError("No initial state found")

    def _assert_final_state(self) -> None:
        final_state = next(filter(attrgetter("final_state"), self.states), None)
        if final_state is None:
            raise ValueError("No final state found")

    @staticmethod
    def get_state_validator(type_: StateTypeEnum) -> Type[StateValidator]:
        return {
            StateTypeEnum.integration: IntegrationStateValidator,
            StateTypeEnum.screen: ScreenStateValidator,
            StateTypeEnum.technical: TechnicalStateValidator,
        }[type_]

    def run(self):
        processed = set()
        for state in self.states:
            if state.name in processed:
                logger.debug(
                    f"Skipping state {state.name} as it has already been processed"
                )
                continue
            state_type = self._assert_type(state)
            validator = self.get_state_validator(state_type)
            state_validator = validator(state=state, context=set(self.automaton_context.keys()))
            state_validator.apply_assert()
            context_vars = state_validator.get_context_variables()
            self.automaton_context[state.name].extend(context_vars)
            processed.add(state.name)


if __name__ == "__main__":
    from workflow_builder.state_parser.contract import EventModel, IntegrationExpressionModel,TransitionModel

    s = AutomatonValidator(
        [
            StateModel(
                state_type="integration",
                name="Q1",
                initial_state=True,
                final_state=True,
                transitions=[
                    TransitionModel(case="submit_form", state_id="next_state")
                ],
                expressions=[IntegrationExpressionModel(
                    variable="form_valid", url="http://localhost:8000", params={}, method="get"
                )],
            )
        ]
    )
    s.run()
