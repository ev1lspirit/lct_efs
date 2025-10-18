import logging
from typing import Optional
from context import SessionContext
from workflow_builder.states import WorkflowState
from workflow_builder.transitions import Transition

logger = logging.getLogger(__name__)

class TransitionCandidateSearcherMixin:
    session_context: SessionContext

    async def _get_transition_candidates_based_on_expressions(
        self, current_state: "WorkflowState"
    ) -> Optional[Transition]:
        logger.info("Proceeding to next state based on expressions...")
        context = await self.session_context.session()
        for expr in current_state.executables:
            if not expr.metadata.bindable():
                continue
            result = await self.session_context.get(expr.metadata.variable)
            logger.debug(f"Processing expression: {expr}, result: {result}")
            executable_transitions = expr.metadata.transition_bind_object
            for transition in executable_transitions:
                logger.debug(f"Evaluating transition: {transition}")
                if transition.case is None or transition.matches(context):
                    logger.info(f"Transition matched: {transition}")
                    return transition

        for transition in current_state.transitions:
            if transition.case is None:
                return transition
        logger.warning("No matching transition found based on expressions.")
        return None

    def _get_transition_candidates_based_on_event(
        self, current_state: "WorkflowState", event_name: str
    ):
        logger.info(f"Processing event '{event_name}' for screen state...")
        for expr in current_state.executables:
            result = expr.result(event_name)
            logger.info(f"Checking handler for event {expr.metadata.event_name}")
            if not result:
                continue
            executable_transitions = expr.metadata.transition_bind_object
            for transition in executable_transitions:
                logger.info(
                    f"Found matching event handler, transition to: {transition.state_id}"
                )
                return transition
