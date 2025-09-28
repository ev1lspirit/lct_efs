from typing import Type
from ..builders.base import BaseHandlersCreator
from ..handlers import IntegrationHandler
# from adapters.commonAdapter import CommonAdapter

class CommonAdapter:
    pass

class WorkflowIntegrationHandlersCreator(BaseHandlersCreator[IntegrationHandler]):
    """ Создатель обработчиков интеграционных состояний """
    adapter: Type['CommonAdapter'] = CommonAdapter

    def __call__(self, **kwargs):
        """
        Calls the parent class's __call__ method with the adapter set to self.adapter.

        Args:
            **kwargs: Keyword arguments to pass to the parent class's __call__ method.

        Returns:
            The result of calling the parent class's __call__ method.
        """
        return super().__call__(adapter=self.adapter(), **kwargs)
