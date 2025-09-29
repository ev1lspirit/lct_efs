from abc import ABC
from typing import Any, Literal, Optional, Union
from pydantic import BaseModel
from workflow_builder.states import IntegrationState, ScreenState, TechnicalState

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
    state_type: Literal["technical", "integration", "screen"]
    name: str
    transitions: list[TransitionModel] = []
    expressions: list[Union[TechnicalExpressionModel, IntegrationExpressionModel, EventModel]] = []
    initial_state: bool = False
    events: list[EventModel] = []
    final_state: bool = False


STATE_CLASSES = {
    "technical": TechnicalState,
    "integration": IntegrationState,
    "screen": ScreenState,
}
