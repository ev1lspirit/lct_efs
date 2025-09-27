from pydantic import BaseModel, ValidationError

from .states import *
from typing import Dict, Any, List, Literal
import logging


class TransitionModel(BaseModel):
    case: str
    state_id: str


class StateModel(BaseModel):
    state_type: Literal["technical", "integration", "screen"]
    name: str = "some-state"
    transitions: List[TransitionModel] = []
    expressions: List[str] = []
    initial_state: bool = False
    final_state: bool = False


STATE_CLASSES = {
    "technical": TechnicalState,
    "integration": IntegrationState,
    "screen": ScreenState,
}

logger = logging.getLogger(__name__)


class GlobalStateParser:
    """
    Класс для парсинга входных данных с админ-панели
    """

    def __init__(self, data: Dict[str, Any]):
        self.data = data

    def parse_states(self) -> List[WorkflowState]:
        states = []

        for raw_state in self.data.get("states", []):
            try:
                state = StateModel(**raw_state)  # валидация
                states.append(self._configure_state_fields(state))
            except ValidationError as ve:
                logger.error(f"Validation error for state: {raw_state} -> {ve}")
                raise
            except Exception as e:
                logger.error(f"Failed to parse state: {raw_state}, error: {e}")
                raise

        return states

    @staticmethod
    def _configure_state_fields(state: StateModel) -> WorkflowState:
        cls = STATE_CLASSES.get(state.state_type)
        if not cls:
            raise ValueError(f"Unsupported state_type: {state.state_type}")

        transitions = [Transition(case=t.case, state_id=t.state_id) for t in state.transitions]

        return cls(
            name=state.name,
            transitions=transitions,
            expressions=state.expressions,
            initial_state=state.initial_state,
            final=state.final_state,
        )


"""
Проверка работоспособности 
"""
if __name__ == "__main__":
    test_json = {
        "states": [
            {
                "state_type": "technical",
                "name": "start",
                "transitions": [
                    {"case": "user_is_authorized", "state_id": "next"}
                ],
                "expressions": ["check_user"],
                "initial_state": True,
                "final_state": False
            },
            {
                "state_type": "screen",
                "name": "next",
                "transitions": [],
                "expressions": ["render_ui"],
                "initial_state": False,
                "final_state": True
            }
        ]
    }

    parser = GlobalStateParser(test_json)
    states = parser.parse_states()

    for s in states:
        print(s)
