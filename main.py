import logging
from workflow_builder.state_parser.parser import GlobalStateParser
from utils import setup_logging
from workflow_builder.automaton.automaton import Automaton

setup_logging()
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    pass

    parser = GlobalStateParser("Init", workflow_id="1234")
    parser.get_automaton_subgraph()
    automaton = Automaton()
    automaton.run()
