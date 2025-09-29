from enum import StrEnum
from typing import Type, TypeVar

from storage.redis import service
from workflow_builder.builders.dependency import WorkflowDependencyHandlersCreator

from .builders.base import BaseHandlersCreator
from .builders.technical import WorkflowTechnicalHandlersCreator
from .builders.integration import WorkflowIntegrationHandlersCreator
from .builders.screen import WorkflowScreenHandlersCreator


StateModel = TypeVar("StateModel")


class StateTypeEnum(StrEnum):
    """ Типы состояний в рамках FSM """
    screen = "screen"
    technical = "technical"
    integration = "integration"
    service = "service"


state_mapping: dict[StateTypeEnum, Type[BaseHandlersCreator]] = {
    StateTypeEnum.technical: WorkflowTechnicalHandlersCreator,
    StateTypeEnum.integration: WorkflowIntegrationHandlersCreator,
    StateTypeEnum.screen: WorkflowScreenHandlersCreator,
    StateTypeEnum.service: WorkflowDependencyHandlersCreator,
}
