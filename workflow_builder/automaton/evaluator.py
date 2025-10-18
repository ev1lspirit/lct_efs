from functools import partial
import logging
import re
from types import CoroutineType
from typing import TYPE_CHECKING, Any, Callable
from attrs import define, field
from workflow_builder.models import StateTypeEnum

if TYPE_CHECKING:
    from workflow_builder.states import WorkflowState
    from context import SessionContext

logger = logging.getLogger(__name__)


class ExpressionEvaluatorMixin:
    session_context: "SessionContext"
    current_state: "WorkflowState"

    async def __process_integration_state_evaluation(self, expression, variable):
        # Для integration states сохраняем JSON-данные ответа API
        logger.info(
            f"Executing integration state for variable: {variable}"
        )
        raw_result = await expression.result()
        logger.info(
            f"Integration raw_result type: {type(raw_result).__name__}"
        )
        # Проверяем, является ли результат объектом с атрибутами
        if hasattr(raw_result, "content"):
            # Это Response объект от API
            result = raw_result.content  # Сохраняем JSON содержимое
            logger.info(
                f"Raw result has 'content' attribute, extracting content"
            )
            logger.info(
                f"Content type: {type(result).__name__}, value: {result}"
            )
        else:
            result = raw_result
            logger.info(
                f"Raw result has no 'content' attribute, using as-is"
            )
            logger.info(
                f"Result type: {type(result).__name__}, value: {result}"
            )
        logger.info(f"About to save to context['{variable}']")
        return result

    async def __evaluate_expression(self, expression , variable, event_name=None):
        try:
            if self.current_state.type_ == StateTypeEnum.screen:
                result = expression.result(event_name)
            elif self.current_state.type_ == StateTypeEnum.integration:
                result = await self.__process_integration_state_evaluation(expression, variable)
            else:
                result = await expression.result()
            logger.info(
                f"Setting context['{variable}'] = {type(result).__name__}"
            )
            logger.info(f"✅ Context updated: {variable} = {result}")
        except Exception as e:
            raise RuntimeError(
                f"Failed to evaluate expression for variable {variable}: {str(e)}"
            ) from e
        return result

    async def _evaluate_executables(self, event_name: str = None):
        async with self.session_context as context:
            for expression in self.current_state.executables:
                # Для screen состояний используем event_name в качестве переменной
                variable = (expression.metadata.event_name
                      if self.current_state.type_ == StateTypeEnum.screen
                      else expression.metadata.variable
                )
                result = await self.__evaluate_expression(expression, variable, event_name)
                context[variable] = result

    async def _evaluate_service_executables(self):
        for expression in self.current_state.executables:
            try:
                await expression.result()
            except Exception as e:
                raise RuntimeError(f"Failed to evaluate expression: {str(e)}")

    def evaluator(self, event_name: str = None) -> Callable[[], CoroutineType[Any, Any, None]] | partial[CoroutineType[Any, Any, None]]:
        if self.current_state.type_ == StateTypeEnum.service:
            return self._evaluate_service_executables
        return partial(self._evaluate_executables, event_name)
