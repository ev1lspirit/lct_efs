from __future__ import annotations
from abc import ABC, ABCMeta
from collections import OrderedDict, defaultdict
from typing import Any, ClassVar, MutableMapping
from attr import define, field, validators as v

from .mixins import AssertCallerMixin
from .transition import IntegrationTransitionValidator, ScreenTransitionValidator, TechnicalTransitionValidator, TransitionValidator
from workflow_builder.state_parser.contract import StateModel


class PreserveMethodOrderMeta(ABCMeta):

    @classmethod
    def __prepare__(metacls, name: str, bases: tuple[type, ...], /, **kwds: Any) -> MutableMapping[str, object]:
        return OrderedDict()


class AbstractMethodOrderPreserver(ABC, PreserveMethodOrderMeta):
    ...


@define(slots=False)
class StateValidator(ABC, AssertCallerMixin, metaclass=AbstractMethodOrderPreserver):
    state: StateModel = field(validator=v.instance_of(StateModel))
    context: set = field(validator=v.instance_of(set))
    transition_validator: TransitionValidator = field(
        validator=v.instance_of(TransitionValidator), init=False)

    _expression_binding_key: ClassVar[str]

    def _assert_from_validators(self):
        return self.transition_validator.apply_assert()

    def _assert_binding_key(self):
        for expression in self.state.expressions:
            if not hasattr(expression, self._expression_binding_key):
                raise ValueError(
                    f"Screen state expression must have {self._expression_binding_key}"
                )

    def _assert_all_transitions_bound(self):
        expressions_list = [exp.variable for exp in self.state.expressions]
        expressions = set(expressions_list)

        transition_binds = defaultdict(list)
        marked_transitions = set()
        for transition in self.state.transitions:
            if transition.variable in expressions:
                matching_expressions = [
                    expression
                    for expression in self.state.expressions
                    if expression.variable == transition.variable
                ]
                transition_binds[transition.variable].extend(matching_expressions)
                marked_transitions.add(transition.variable)
            else:
                raise ValueError(f"Unbound transtion found: {transition.variable}")

    def get_context_variables(self):
        return set(
            getattr(expr, self._expression_binding_key)
            for expr in self.state.expressions
        )

    def _assert_context_dependency(self): ...


@define
class IntegrationStateValidator(StateValidator):
    _expression_binding_key: ClassVar[str] = "variable"

    def __attrs_post_init__(self):
        self.transition_validator = IntegrationTransitionValidator(self.state)

    def _assert_transition_count(self):
        if len(self.state.transitions) == 0:
            raise ValueError("Integration state must have at least one transition")
        if len(self.state.transitions) > 1:
            raise ValueError(
                f"Only one transition is allowed per state, got {len(self.state.transitions)}"
            )
        if self.state.transitions[0].case is not None:
            raise ValueError(
                f"Integration state can't have a transition condition: {self.state.transitions[0]}"
            )

    def _assert_context_dependency(self):
        for expr in self.state.expressions:
            if set(expr.dependent_variables) - set(self.context):
                raise ValueError(
                    f"Expression {expr} has dependent variables that are not in context"
                )

@define
class ScreenStateValidator(StateValidator):
    _expression_binding_key = "event_name"

    def __attrs_post_init__(self):
        self.transition_validator = ScreenTransitionValidator(self.state)

    def _assert_all_transitions_bound(self):
        attr_callable = lambda expr: getattr(expr, self._expression_binding_key, None)
        items_found = set(attr_callable(expr) for expr in self.state.expressions)
        if None in items_found:
            raise ValueError(
                "One or more expressions in the screen state are missing the required attribute "
                f"'{self._expression_binding_key}'. Expressions found: "
                f"{[expr for expr in self.state.expressions]}.\n"
                f"Events missing '{self._expression_binding_key}': "
                f"{[expr for expr in self.state.expressions if attr_callable(expr) is None]}"
            )
        processed_events = set()
        for transition in self.state.transitions:
            if transition.case in items_found:
                if transition.case in processed_events:
                    raise ValueError(
                        f"Duplicate transition for event {transition.case}"
                    )
                processed_events.add(transition.case)
            else:
                raise ValueError(
                    f"Event {transition.case} not found in provided events"
                )

@define
class TechnicalStateValidator(StateValidator):
    _expression_binding_key = "variable"


    def __attrs_post_init__(self):
        self.transition_validator = TechnicalTransitionValidator(self.state)

    # def _assert_context_dependency(self):
    #     for expr in self.state.expressions:
    #         if set(expr.dependent_variables) - self.context:
    #             raise ValueError(
    #                 f"Expression {expr} has dependent variables that are not in context"
    #             )
