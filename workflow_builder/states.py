from __future__ import annotations
from functools import cached_property
from context import SessionContext
from abc import ABC
from typing import ClassVar
import uuid
import json
from workflow_builder.transitions import Transition
from .models import StateTypeEnum, state_mapping
from database.redis.service import RedisCache


class WorkflowState(ABC):
    """Базовое состояние"""

    type_: ClassVar[StateTypeEnum]
    context: ClassVar[SessionContext] = {}

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
        self._configure_transitions()

    @cached_property
    def transition_map(self) -> dict[str, Transition]:
        return {t.state_id: t for t in self.transitions}

    def _create_exec_handlers(self, **kwargs):
        creator = self._resolve_exec_creator()
        return creator(**kwargs)

    def _resolve_exec_creator(self):
        handlers_creator = state_mapping.get(self.type_)
        if handlers_creator is None:
            return lambda: {}
        return handlers_creator(workflow_state=self, handlers=self.expressions)

    def _configure_transitions(self):
        self._bind_transitions(entity="expressions")

    def _bind_transitions(self, entity="expressions"):
        entity_value = getattr(self, entity, None)
        if entity_value is None:
            raise ValueError(f"{entity} is not found in class {self.__class__.__name__}")

        bind_map = self.transition_map
        for expr in entity_value:
            transition = bind_map.get(expr.transition_bind)
            if transition is None:
                raise ValueError(f"Transition with id={expr.transition_bind} not found")
            expr.transition_bind_object = transition

    def __repr__(self):
        return f"<{self.__class__.__name__} uid={self.uid} type={self.type_}>"


class TechnicalState(WorkflowState):
    type_ = StateTypeEnum.technical


class IntegrationState(WorkflowState):
    type_ = StateTypeEnum.integration


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

    def _configure_transitions(self):
        self._bind_transitions(entity="expressions")

    def send_to_front(self) -> dict:
        """Получает экран из Redis по имени этого состояния и возвращает JSON для фронта"""
        redis_cache = RedisCache()
        screen_key = redis_cache.get_screen_key(self.name)
        screen_data = redis_cache.r.get(screen_key)

        if not screen_data:
            raise ValueError(f"Screen '{self.name}' not found in Redis")

        return json.loads(screen_data)
