from enum import StrEnum
from typing import Type, TypeVar

from .builders.base import BaseHandlersCreator
from .builders.technical import WorkflowTechnicalHandlersCreator


StateModel = TypeVar("StateModel")


class StateTypeEnum(StrEnum):
    screen = "SCREEN"
    technical = "TECHNICAL"
    integration = "INTEGRATION"


state_mapping: dict[StateTypeEnum, Type[BaseHandlersCreator]] = {
    StateTypeEnum.technical: WorkflowTechnicalHandlersCreator,
    # StateTypeEnum.screen: WorkflowScreenHandlersCreator,
    # StateTypeEnum.integration: WorkflowIntegrationHandlersCreator,
}
