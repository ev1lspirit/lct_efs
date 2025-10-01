from typing import Any, Literal, Optional, Union
from pydantic import BaseModel, model_validator
from workflow_builder.expressions import ServiceStateExpression, Expression
from workflow_builder.states import (
    IntegrationState,
    ScreenState,
    ServiceState,
    TechnicalState,
)
from config import settings


class TransitionModel(BaseModel):
    case: Optional[str]
    state_id: str
    variable: Optional[Union[str, list]] = None


class TechnicalExpressionModel(BaseModel):
    variable: str  # variable to be updated
    dependent_variables: list[str]  # a list of dependent variables
    expression: str  # python execution lambda


class IntegrationExpressionModel(BaseModel):
    variable: str
    url: str
    params: dict[str, Any]
    method: Literal["get", "post", "put", "delete", "patch"]


class EventModel(BaseModel):
    event_name: str


class StateModel(BaseModel):
    state_type: Literal["technical", "integration", "screen", "service"]
    name: str
    screen: dict = {}
    transitions: list[TransitionModel] = []
    expressions: list[
        Union[
            TechnicalExpressionModel,
            IntegrationExpressionModel,
            EventModel
        ]
    ] = []
    initial_state: bool = False
    events: list[EventModel] = []
    final_state: bool = False

    @classmethod
    def zero_state(cls, next_state_name: str):
        return cls(
            state_type="service",
            name=settings.SERVICE_INIT_STATE,
            transitions=[
                TransitionModel(case=None, state_id=next_state_name, variable=None)
            ],
            initial_state=True,
            expressions=[],
            events=[],
            final_state=False,
        )

    @classmethod
    def error_state(cls):
        return cls(
            state_type="service",
            name=settings.SERVICE_ERROR_STATE,
            transitions=[],
            initial_state=False,
            expressions=[],
            events=[],
            final_state=True,
        )


class StateSet(BaseModel):
    states: list[StateModel]

    @model_validator(mode="before")
    def validate_states(cls, values):
        states = values.get("states", [])
        if not states:
            return values

        initial_states = [state for state in states if state.get("initial_state")]
        final_states = [state for state in states if state.get("final_state")]

        if len(initial_states) != 1:
            raise ValueError(
                "There must be exactly one state with 'initial_state' set to True."
            )
        if not final_states:
            raise ValueError(
                "There must be at least one state with 'final_state' set to True."
            )

        return values


STATE_CLASSES = {
    "technical": TechnicalState,
    "integration": IntegrationState,
    "screen": ScreenState,
    "service": ServiceState,
}
