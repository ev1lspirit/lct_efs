import logging
from context import SessionContext
context = SessionContext({"z": 1, "y": 7, "l": 4, "balance": 100, "x": -1})
from utils import setup_logging
from workflow_builder.automaton.automaton import Automaton
from workflow_builder.expressions import Expression
from workflow_builder.states import IntegrationState, ScreenState, TechnicalState
from workflow_builder.transitions import Transition


setup_logging()
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    pass
