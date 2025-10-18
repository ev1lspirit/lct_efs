from typing import Any, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from workflow_builder.models import StateTypeEnum
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
    params: Optional[dict[str, Any]] = None
    body: Optional[dict[str, Any]] = None
    method: Literal["get", "post", "put", "delete", "patch"]
    dependent_variables: Optional[list[str]] = None
    error_variable: Optional[str] = None

    @model_validator(mode='after')
    def validate_params_or_body(self):
        """Validation: GET/DELETE should use params, POST/PUT/PATCH should use body"""
        method = self.method.lower()
        
        if self.dependent_variables is None:
            self.dependent_variables = []

        if method in ['get', 'delete']:
            if self.body is not None:
                raise ValueError(f"Method '{method}' should use 'params', not 'body'")
        elif method in ['post', 'put', 'patch']:
            if self.params is not None and self.body is None:
                raise ValueError(f"Method '{method}' should use 'body', not 'params'")

        return self


class EventModel(BaseModel):
    event_name: str


class StateModel(BaseModel):
    state_type: Literal["technical", "integration", "screen", "service"]
    name: str
    screen: dict = Field(default_factory=dict)
    transitions: list[TransitionModel] = Field(default_factory=list)
    expressions: list[
        Union[
            TechnicalExpressionModel,
            IntegrationExpressionModel,
            EventModel
        ]
    ] = Field(default_factory=list)
    initial_state: bool = False
    events: list[EventModel] = Field(default_factory=list)
    final_state: bool = False

    @field_validator("expressions", mode="after")
    def validate_events(cls, value: list[EventModel], info):
        type_ = StateTypeEnum(info.data.get("state_type"))
        if type_ == StateTypeEnum.service:
            return value

        types_ = {
            StateTypeEnum.screen: EventModel,
            StateTypeEnum.technical: TechnicalExpressionModel,
            StateTypeEnum.integration: IntegrationExpressionModel
        }

        if any(
            map(lambda x: type(x) is not types_[type_],
                value)
        ):
            raise ValueError(
                f"State type {type_} can't have expressions of type {types_[type_]}")
        return value

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
        # Handle both cases: dict with "states" key or direct list
        if isinstance(values, list):
            # If values is already a list, wrap it in a dict
            values = {"states": values}

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
