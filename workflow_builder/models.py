from enum import StrEnum
from typing import Type, TypeVar

from .builders.base import BaseHandlersCreator
from .builders.technical import WorkflowTechnicalHandlersCreator
from .builders.integration import WorkflowIntegrationHandlersCreator
from .builders.screen import WorkflowScreenHandlersCreator


StateModel = TypeVar("StateModel")


class StateTypeEnum(StrEnum):
    """ Типы состояний в рамках FSM"""
    screen = "SCREEN"
    technical = "TECHNICAL"
    integration = "INTEGRATION"


state_mapping: dict[StateTypeEnum, Type[BaseHandlersCreator]] = {
    StateTypeEnum.technical: WorkflowTechnicalHandlersCreator,
    StateTypeEnum.integration: WorkflowIntegrationHandlersCreator,
    StateTypeEnum.screen: WorkflowScreenHandlersCreator,
}
