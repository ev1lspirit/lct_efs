from __future__ import annotations
from collections import defaultdict
from functools import cached_property
import logging
from context import SessionContext
from abc import ABC
from typing import ClassVar
import uuid
import json
from workflow_builder.transitions import Transition
from .models import StateTypeEnum, state_mapping
# from database.redis.service import RedisCache


logger = logging.getLogger(__name__)

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
        self._bind_transitions()

    @cached_property
    def transition_map(self) -> dict[str, list[Transition]]:
        default_transitions = defaultdict(list)
        if self.type_ == StateTypeEnum.screen:
            attr = "case"
        else:
            attr = "variable"
        for t in self.transitions:
            default_transitions[getattr(t, attr)].append(t)
        return default_transitions

    def _create_exec_handlers(self, **kwargs):
        creator = self._resolve_exec_creator()
        return creator(**kwargs)

    def _resolve_exec_creator(self):
        handlers_creator = state_mapping.get(self.type_)
        if handlers_creator is None:
            return lambda: {}
        return handlers_creator(workflow_state=self, handlers=self.expressions)

    def _bind_transitions(self):
        binding_key = "event_name" if self.type_ == StateTypeEnum.screen else "variable"
        bind_map = self.transition_map
        for expr in self.expressions:
            transitions = bind_map.get(getattr(expr, binding_key), [])
            expr.transition_bind_object = transitions

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
    def send_to_front(self) -> dict:
        """Получает экран из Redis по имени этого состояния и возвращает JSON для фронта"""
        redis_cache = {}
        screen_key = redis_cache.get_screen_key(self.name)
        screen_data = redis_cache.r.get(screen_key)

        if not screen_data:
            raise ValueError(f"Screen '{self.name}' not found in Redis")
        return json.loads(screen_data)
