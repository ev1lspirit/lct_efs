from typing import Type
from ..builders.base import BaseHandlersCreator
from ..handlers import IntegrationHandler

class CommonAdapter:
    pass

class WorkflowIntegrationHandlersCreator(BaseHandlersCreator[IntegrationHandler]):
    """ Создатель обработчиков интеграционных состояний """
    adapter: Type['CommonAdapter'] = CommonAdapter

    def __call__(self, **kwargs):
        return super().__call__(adapter=self.adapter(), **kwargs)
