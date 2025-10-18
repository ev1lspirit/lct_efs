from abc import ABC
from attrs import define, field, validators as v
from .mixins import AssertCallerMixin
from workflow_builder.state_parser.contract import StateModel
import logging

logger = logging.getLogger()


@define
class TransitionValidator(ABC, AssertCallerMixin):
    state: StateModel = field(validator=v.instance_of(StateModel))

    def _assert_type_dependent_structure(self):
        for transition in self.state.transitions:
            if transition.variable is None:
                raise ValueError(f"Variable can't be None")

    def _assert_deterministic(self):
        processed = set()
        for transition in self.state.transitions:
            pair = (transition.variable, transition.case)
            if pair in processed:
                raise ValueError(f"Automaton is not deterministic. Detected several transitions by {transition.variable}")
            processed.add(pair)

    def __call__(self):
        for key, asserter in vars(self.__class__).items():
            if key.startswith("_assert") and callable(asserter):
                logger.info(f"Calling asserter: {key}")
                asserter()


class IntegrationTransitionValidator(TransitionValidator):
    ...


class TechnicalTransitionValidator(TransitionValidator):
    ...


class ScreenTransitionValidator(TransitionValidator):

    def _assert_deterministic(self):
        events = set()
        for transition in self.state.transitions:
            if transition.case in events:
                raise ValueError(
                    f"Automaton is not deterministic. Detected several transitions by event {transition.case}"
                )
            events.add(transition.case)

    def _assert_type_dependent_structure(self):
        for transition in self.state.transitions:
            if transition.variable:
                raise ValueError(
                    f"Variables are prohibited in the screen state"
                )
