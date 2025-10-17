from __future__ import annotations
from functools import cached_property
import logging
from abc import ABC
from typing import ClassVar
import uuid
import json
from context import SessionContext
from workflow_builder.transitions import Transition
from .models import StateTypeEnum, state_mapping
# from database.redis.service import RedisCache


logger = logging.getLogger(__name__)

class WorkflowState(ABC):
    """Базовое состояние"""

    type_: ClassVar[StateTypeEnum]

    def __init__(
        self,
        context: SessionContext,
        name: str,
        transitions: list[Transition],
        expressions: list,
        initial_state: bool = False,
        final: bool = False,
    ):
        self.uid = uuid.uuid4()
        self.context = context
        self.name = name
        self.initial_state = initial_state
        self._final = final
        self.state_local_context = {}
        self.expressions: list = expressions
        self.transitions = transitions
        
        logger.debug(
            f"Creating state '{name}' (type={getattr(self, 'type_', 'unknown')}): "
            f"{len(expressions)} expressions, {len(transitions)} transitions"
        )
        
        self.executables = self._create_exec_handlers()
        self._bind_transitions()

    @cached_property
    def transition_map(self): #-> dict[str, list[Transition]]:
        return self.transitions

    def _create_exec_handlers(self, **kwargs):
        creator = self._resolve_exec_creator()
        return creator(**kwargs)

    def _resolve_exec_creator(self):
        handlers_creator = state_mapping.get(self.type_)
        if handlers_creator is None:
            return lambda: {}
        return handlers_creator(context=self.context, workflow_state=self, handlers=self.expressions)

    def _bind_transitions(self):
        binding_key = "keys" if self.type_ == StateTypeEnum.screen else "variables"
        binding_expression_key = "event_name" if self.type_ == StateTypeEnum.screen else "variable"
        
        logger.debug(
            f"Binding transitions for state '{self.name}' (type={self.type_}): "
            f"binding_key='{binding_key}', binding_expression_key='{binding_expression_key}'"
        )
        
        for idx, expr in enumerate(self.expressions):
            if not expr.bindable():
                logger.debug(f"  Expression [{idx}] is not bindable, skipping")
                continue

            expr_binding_value = getattr(expr, binding_expression_key, None)
            logger.debug(f"  Expression [{idx}] {binding_expression_key}='{expr_binding_value}'")
            
            expr.transition_bind_object = [
                t for t in self.transitions if {getattr(expr, binding_expression_key)} & getattr(t, binding_key)
            ]
            
            logger.debug(
                f"    Bound to {len(expr.transition_bind_object)} transition(s): "
                f"{[t.state_id for t in expr.transition_bind_object]}"
            )
            
            if self.type_ == StateTypeEnum.integration:
                transition_count = len(expr.transition_bind_object)
                if transition_count != 1:
                    expr_var = getattr(expr, binding_expression_key, "unknown")
                    
                    # Дополнительная диагностика
                    all_transition_vars = []
                    for t in self.transitions:
                        t_vars = getattr(t, 'variables', set())
                        all_transition_vars.append(f"{t.state_id} -> variables: {t_vars}")
                    
                    error_msg = (
                        f"Integration state '{self.name}' can have only one transition per expression.\n"
                        f"  Expression variable: '{expr_var}'\n"
                        f"  Transitions bound: {transition_count}\n"
                    )
                    
                    if transition_count == 0:
                        error_msg += (
                            f"  ❌ No transitions reference variable '{expr_var}'\n"
                            f"  💡 Solution: Add 'variables: [\"{expr_var}\"]' to one of the transitions\n"
                            f"\n  Available transitions:\n    " + "\n    ".join(all_transition_vars)
                        )
                    else:
                        bound_states = [t.state_id for t in expr.transition_bind_object]
                        error_msg += (
                            f"  ❌ Multiple transitions reference variable '{expr_var}'\n"
                            f"  Bound to: {bound_states}\n"
                            f"  💡 Solution: Keep only ONE transition with this variable"
                        )
                    
                    raise ValueError(error_msg)
                    
                if expr.transition_bind_object[0].case is not None:
                    expr_var = getattr(expr, binding_expression_key, "unknown")
                    transition = expr.transition_bind_object[0]
                    raise ValueError(
                        f"Integration state '{self.name}' can't have a transition condition.\n"
                        f"  Expression variable: '{expr_var}'\n"
                        f"  Transition to: '{transition.state_id}'\n"
                        f"  ❌ Has condition: {transition.case}\n"
                        f"  💡 Solution: Remove 'case' field from the transition (set to null)"
                    )

    def __repr__(self):
        return f"<{self.__class__.__name__} uid={self.uid} type={self.type_}>"


class TechnicalState(WorkflowState):
    type_ = StateTypeEnum.technical


class IntegrationState(WorkflowState):
    type_ = StateTypeEnum.integration


class ScreenState(WorkflowState):
    type_ = StateTypeEnum.screen
    


class ServiceState(WorkflowState):
    type_ = StateTypeEnum.service

    # def __init__(
    #     self,
    #     name: str,
    #     final: bool,
    #     transitions: list[Transition],
    #     expressions: list,
    #     initial_state: bool = False,
    # ):
    #     super().__init__(name=name, final=final, transitions=transitions, expressions=expressions, initial_state=initial_state)

    def send_to_front(self) -> dict:
        """Получает экран из Redis по имени этого состояния и возвращает JSON для фронта"""
        redis_cache = {}
        screen_key = redis_cache.get_screen_key(self.name)
        screen_data = redis_cache.r.get(screen_key)

        if not screen_data:
            raise ValueError(f"Screen '{self.name}' not found in Redis")
        return json.loads(screen_data)


class SubflowState(WorkflowState):
    """State for calling another workflow as a subprocess"""
    type_ = StateTypeEnum.subflow
