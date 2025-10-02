from enum import Enum
from typing import Type, TypeVar

from workflow_builder.builders.dependency import WorkflowServiceHandlersCreator

from .builders.base import BaseHandlersCreator
from .builders.technical import WorkflowTechnicalHandlersCreator
from .builders.integration import WorkflowIntegrationHandlersCreator
from .builders.screen import WorkflowScreenHandlersCreator


StateModel = TypeVar("StateModel")


class StateTypeEnum(str, Enum):
    """Типы состояний в рамках FSM"""

    screen = "screen"
    technical = "technical"
    integration = "integration"
    service = "service"


state_mapping: dict[StateTypeEnum, Type[BaseHandlersCreator]] = {
    StateTypeEnum.technical: WorkflowTechnicalHandlersCreator,
    StateTypeEnum.integration: WorkflowIntegrationHandlersCreator,
    StateTypeEnum.screen: WorkflowScreenHandlersCreator,
    StateTypeEnum.service: WorkflowServiceHandlersCreator,
}
