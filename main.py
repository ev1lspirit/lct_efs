import logging
from context import SessionContext
context = SessionContext({"z": 1, "y": 7, "l": 4, "balance": 100, "x": -1, "records": {'type': 'B'}})
from workflow_builder.state_parser.parser import GlobalStateParser
from utils import setup_logging
from workflow_builder.automaton.automaton import Automaton
from workflow_builder.expressions import Expression
from workflow_builder.states import IntegrationState, ScreenState, TechnicalState
from workflow_builder.transitions import Transition


setup_logging()
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    test_json = {
        "states": [
            {
                "state_type": "technical",
                "name": "Init",
                "transitions": [
                    {"variable": "data_loaded", "case": "True", "state_id": "ProcessData"},
                    {"variable": "data_loaded", "case": "False", "state_id": "ErrorState"},
                ],
                "expressions": [
                    {
                        "variable": "data_loaded",
                        "dependent_variables": [],
                        "expression": "True",
                    }
                ],
                "initial_state": True,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "ProcessData",
                "transitions": [
                    {
                        "variable": "is_type_a",
                        "case": "True",
                        "state_id": "ShowScreenA",
                    },
                    {
                        "variable": "is_type_b",
                        "case": "True",
                        "state_id": "ShowScreenB",
                    },
                    {
                        "variable": ["is_type_a", "is_type_b"],
                        "case": "False",
                        "state_id": "ErrorState",
                    },
                ],
                "expressions": [
                    {
                        "variable": "is_type_a",
                        "dependent_variables": ["records"],
                        "expression": "records['type'] == 'A'",
                    },
                    {
                        "variable": "is_type_b",
                        "dependent_variables": ["records"],
                        "expression": "records['type'] == 'B'",
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "ShowScreenA",
                "transitions": [
                    {"case": "continue", "state_id": "Final"},
                    {"case": "back", "state_id": "ProcessData"},
                ],
                "expressions": [
                    {"event_name": "continue"},
                    {"event_name": "back"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "ShowScreenB",
                "transitions": [
                    {"case": "continue", "state_id": "Final"},
                    {"case": "back", "state_id": "ProcessData"},
                ],
                "expressions": [
                    {"event_name": "continue"},
                    {"event_name": "back"},
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "technical",
                "name": "Final",
                "transitions": [],
                "expressions": [],
                "initial_state": False,
                "final_state": True,
            },
            {
                "state_type": "technical",
                "name": "ErrorState",
                "transitions": [],
                "expressions": [],
                "initial_state": False,
                "final_state": True,
            },
        ]
    }

    parser = GlobalStateParser(current_state_name="Init", data=test_json)
    states = parser.get_automaton_subgraph()

    automaton = Automaton(states)
    automaton.run()
