from workflow_builder.builders.base import BaseHandlersCreator
from workflow_builder.handlers import DependencyHandler


class WorkflowDependencyHandlersCreator(BaseHandlersCreator[DependencyHandler]):
    """Создатель обработчиков технических состояний"""
