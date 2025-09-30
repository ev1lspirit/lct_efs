from workflow_builder.builders.base import BaseHandlersCreator
from workflow_builder.handlers import DependencyHandler
from workflow_builder.handlers import BehaviourTypeEnum


class WorkflowServiceHandlersCreator(BaseHandlersCreator[DependencyHandler]):
    """Создатель обработчиков технических состояний"""

    def __call__(self, **kwargs):
        """
        Calls the parent class's __call__ method with the adapter set to self.adapter.

        Args:
            **kwargs: Keyword arguments to pass to the parent class's __call__ method.

        Returns:
            The result of calling the parent class's __call__ method.
        """
        behaviour_str = self.workflow_state.name.split("_")
        behaviour = BehaviourTypeEnum(behaviour_str[-1])
        return super().__call__(behaviour_type=behaviour, **kwargs)
