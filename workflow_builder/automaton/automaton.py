import asyncio
from functools import partial
import logging
import time
from typing import TYPE_CHECKING, Optional

from attrs import define, field
from context import SessionContext
from workflow_builder.automaton.constructor import StateConstructor
from workflow_builder.automaton.evaluator import  ExpressionEvaluatorMixin
from workflow_builder.automaton.mixins import TransitionCandidateSearcherMixin
from workflow_builder.automaton.models import StateMetadata
from workflow_builder.models import StateTypeEnum
from config import settings
from storage.mongo.client import MongoDBClient

if TYPE_CHECKING:
    from ..states import WorkflowState

logger = logging.getLogger(__name__)


@define
class Automaton(TransitionCandidateSearcherMixin, ExpressionEvaluatorMixin):
    session_id: str = field()
    workflow_id: str = field()
    zero_state: str = field(default=settings.SERVICE_INIT_STATE)

    initial_state_name: str = field(default=None)
    state_constructor: StateConstructor = field(init=False)

    states: list["WorkflowState"] = field(factory=list)
    state_mapping: dict[str, "WorkflowState"] = field(factory=dict)
    _current_state: Optional["WorkflowState"] = field(default=None)
    _actual_initial_state: "WorkflowState" = field(default=None)

    def __attrs_post_init__(self):
        self.session_context = SessionContext(
            session_id=self.session_id, workflow_id=self.workflow_id
        )

    async def __aenter__(self):
        self.initial_state_name = (await self._resolve_initial_state()).name
        self.state_constructor = StateConstructor(self.session_context, self.initial_state_name, self.workflow_id, self.session_id)  # type: ignore # no
        self.states = self.state_constructor.create_states()
        self.state_mapping = {state.name: state for state in self.states}
        self._current_state = self.state_mapping.get(self.zero_state)
        self._actual_initial_state = self.state_mapping[self.initial_state_name]
        return self

    async def __aexit__(self, exc_type, exc_value, traceback): ...

    @property
    def current_state(self) -> "WorkflowState":
        return self._current_state

    @current_state.setter
    def current_state(self, state: "WorkflowState"):
        if state is None:
            raise ValueError("No initial state found")
        self._current_state = state

    async def _resolve_initial_state(self) -> StateMetadata:
        return await self.session_context.get_session_state()

    async def _call_state_checkpoint(self) -> None:
        try:
            current_state_data = StateMetadata(
                name=self.current_state.name, type_=self.current_state.type_
            )
            await self.session_context.update_session_state(current_state_data)
        except Exception as e:
            logger.error(f"Failed to update session state. Error: {e}")
            raise e

    def _get_on_return_policy(self):
        on_return = True
        if self._actual_initial_state.type_ == StateTypeEnum.screen:
            if self.initial_state_name != settings.SERVICE_INIT_STATE:
                on_return = False

        return on_return

    def __get_screen(self) -> Optional[dict]:
        try:
            screens_client = MongoDBClient(
                database=settings.MONGO_DB,
                collection=settings.SCREENS_MONGO_COLLECTION,
            )
            screen_doc = screens_client.get_screen_by_keys(
                self.workflow_id, self.current_state.name
            )
            if screen_doc:
                return screen_doc.get("screen")
            logger.warning(
                f"Screen JSON not found for workflow={self.workflow_id}, state={self.current_state.name}"
            )
            return None
        except Exception as e:
            logger.error(
                f"Failed to retrieve screen for wf={self.workflow_id}, state={self.current_state.name}: {e}"
            )
            return None

    async def run(self, event_name: Optional[str]):
        logger.info("=" * 80)
        logger.info(self)
        logger.info(
            f"🚀 STARTING WORKFLOW EXECUTION | Session: {self.session_id[:8]}... | Workflow: {self.workflow_id[:8]}..."
        )
        logger.info(
            f"📍 Initial state: '{self.current_state.name}' ({self.current_state.type_.value})"
        )
        if event_name:
            logger.info(f"📨 Event: '{event_name}'")
        logger.info("=" * 80)

        start_time = time.time()
        on_return = self._get_on_return_policy()

        while True:
            if self.current_state._final:
                total_execution_time = time.time() - start_time
                logger.info("=" * 80)
                logger.info(
                    f"🏁 WORKFLOW COMPLETED | Final state: '{self.current_state.name}' | "
                    f"Time: {total_execution_time*1000:.2f}ms ({total_execution_time:.4f}s)"
                )
                logger.info("=" * 80)
                break

            # Засекаем время начала выполнения состояния
            state_start_time = time.time()

            if self.current_state.type_ == StateTypeEnum.screen:
                if on_return:
                    # returns screen data
                    await self._call_state_checkpoint()
                    # Сохраняем контекст перед возвратом экрана
                    await self.session_context.update_session()
                    return self.__get_screen()
                on_return = not on_return
                candidate = self._get_transition_candidates_based_on_event(
                    current_state=self.current_state, event_name=event_name
                )
            else:
                # Логируем начало выполнения non-screen состояния
                logger.info(
                    f"⏱️  Executing {self.current_state.type_.value} state: '{self.current_state.name}'"
                )
                evaluator = self.evaluator(event_name=event_name)
                await evaluator()

                # Замеряем время выполнения и логируем
                state_execution_time = time.time() - state_start_time
                logger.info(
                    f"✅ Completed {self.current_state.type_.value} state: '{self.current_state.name}' "
                    f"in {state_execution_time*1000:.2f}ms ({state_execution_time:.4f}s)"
                )

                candidate = self._get_transition_candidates_based_on_expressions(
                    current_state=self.current_state
                )
            if candidate is None:
                logger.error(
                    f"No matching transition found: state: {self.current_state.type_}, {self.current_state.name}"
                )
                raise ValueError("No matching transition found")

            next_state_name = candidate.state_id
            # Логируем переход между состояниями
            logger.info(
                f"🔄 STATE TRANSITION: '{self.current_state.name}' ({self.current_state.type_.value}) "
                f"→ '{next_state_name}'"
            )
            next_state_object = self.state_mapping.get(next_state_name)
            if next_state_object is None:
                logger.error(
                    f"Next state {next_state_name} not found. Check if it was created."
                )
                raise ValueError(
                    f"Next state {next_state_name} not found. Check if it was created."
                )
            self.current_state = next_state_object
            logger.info(
                f"✅ Now in state: '{self.current_state.name}' ({self.current_state.type_.value})"
            )

    def __repr__(self):
        return f"<{self.__class__.__name__} states={self.states}>"


async def main():
    async with Automaton(session_id="1234", workflow_id="1234") as automaton:
        await automaton.run(event_name=None)


if __name__ == "__main__":
    asyncio.run(main())
