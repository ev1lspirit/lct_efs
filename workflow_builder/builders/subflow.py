from typing import Type
from ..builders.base import BaseHandlersCreator
from ..handlers import SubflowHandler


class WorkflowSubflowHandlersCreator(BaseHandlersCreator[SubflowHandler]):
    """Создатель обработчиков субфлоу состояний"""

    def __call__(self, **kwargs):
        """
        Calls the parent class's __call__ method.

        Args:
            **kwargs: Keyword arguments to pass to the parent class's __call__ method.

        Returns:
            The result of calling the parent class's __call__ method.
        """
        return super().__call__(**kwargs)

