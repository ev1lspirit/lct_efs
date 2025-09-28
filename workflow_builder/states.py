from __future__ import annotations
from functools import cached_property
import logging
from abc import ABC, abstractmethod
from typing import ClassVar, Optional, Dict, Any
import uuid
from workflow_builder.transitions import Transition
from .models import StateTypeEnum, state_mapping

logger = logging.getLogger(__name__)

class WorkflowState(ABC):
    """Базовое состояние"""

    type_: ClassVar[StateTypeEnum]
    context: ClassVar = {}

    def __init__(
        self,
        name: str,
        transitions: list[Transition],
        expressions: list,
        initial_state: bool = False,
        final: bool = False,
    ):
        self.uid = uuid.uuid4()
        self.name = name
        self.initial_state = initial_state
        self._final = final
        self.state_local_context = {}
        self.expressions: list = expressions
        self.transitions = transitions
        self.executables = self._create_exec_handlers()
        self._bind_transitions()

    @cached_property
    def transition_map(self):
        return self.transitions

    def _create_exec_handlers(self, **kwargs):
        creator = self._resolve_exec_creator()
        return creator(**kwargs)

    def _resolve_exec_creator(self):
        handlers_creator = state_mapping.get(self.type_)
        if handlers_creator is None:
            return lambda: {}
        return handlers_creator(workflow_state=self, handlers=self.expressions)

    def _bind_transitions(self):
        binding_key = "keys" if self.type_ == StateTypeEnum.screen else "variables"
        binding_expression_key = "event_name" if self.type_ == StateTypeEnum.screen else "variable"
        for expr in self.expressions:
            expr.transition_bind_object = [
                t for t in self.transitions if {getattr(expr, binding_expression_key)} & getattr(t, binding_key)
            ]

    @abstractmethod
    def send_to_front(self) -> Optional[Dict[str, Any]]:
        """Отправляет данные состояния на фронт. Только ScreenState возвращает данные экрана."""
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__} uid={self.uid} type={self.type_}>"


class TechnicalState(WorkflowState):
    type_ = StateTypeEnum.technical

    def send_to_front(self) -> Optional[Dict[str, Any]]:
        """Техническое состояние не отправляет данные на фронт"""
        return None


class IntegrationState(WorkflowState):
    type_ = StateTypeEnum.integration

    def send_to_front(self) -> Optional[Dict[str, Any]]:
        """Интеграционное состояние не отправляет данные на фронт"""
        return None


class ScreenState(WorkflowState):
    type_ = StateTypeEnum.screen

    def __init__(
        self,
        name: str,
        final: bool,
        transitions: list[Transition],
        expressions: list,
        initial_state: bool = False,
    ):
        super().__init__(name=name, final=final, transitions=transitions, expressions=expressions, initial_state=initial_state)

    def send_to_front(self) -> Dict[str, Any]:
        """Получает экран из MongoDB и отправляет JSON на фронт как есть"""
        try:
            from storage.mongo.screen_service import get_screen_service
            screen_service = get_screen_service()
            screen_data = screen_service.get_screen(self.name)

            if not screen_data:
                raise ValueError(f"Screen '{self.name}' not found in MongoDB")

            return screen_data

        except ImportError as e:
            logger.error(f"Failed to import screen_service: {e}")
            raise ValueError(f"Screen service not available: {e}")
        except Exception as e:
            logger.error(f"Error loading screen '{self.name}': {e}")
            raise ValueError(f"Failed to load screen '{self.name}': {e}")
