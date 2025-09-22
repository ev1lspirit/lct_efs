from typing import Type
from ..builders.base import BaseHandlersCreator
from ..handlers import IntegrationHandler


class CommonAdapter:

    def __init__(self, *args, **kwargs):
        pass


class WorkflowIntegrationHandlersCreator(BaseHandlersCreator[IntegrationHandler]):
    adapter: Type[CommonAdapter] = CommonAdapter

    def __call__(self):
        handlers = []
        for state_meta in self.handlers:
            model = self.create_handler(
                state_meta, handler_context=self.context, adapter=self.adapter
            )
            handlers.append(model)
        return handlers
