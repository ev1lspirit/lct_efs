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
    obj = TechnicalState(
        name="Q1",
        initial_state=True,
        transitions=[Transition(case="True", state_id="Q2")],
        expressions=[
            (
                Expression.technical(
                    dependent_variables=["balance"], expression="balance>0"
                )
                & Expression.technical(dependent_variables=["x"], expression="x>0")
            ).bind_transition(name="Q2")
        ],
    )
    integration = ScreenState(
        name="Q2",
        final=False,
        transitions=[],
        expressions=["next"]
    )

    automaton = Automaton(states=[obj, integration])
    runner = automaton.run()

    try:
        next(runner)
    except StopIteration:
        logger.error("Pipeline cannot be continued")

    var = runner.send("next")
