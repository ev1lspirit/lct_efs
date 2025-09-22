from .base import BaseHandlersCreator
from ..handlers import TechnicalHandler
from collections import defaultdict


class WorkflowTechnicalHandlersCreator(BaseHandlersCreator[TechnicalHandler]):

    def __call__(self):
        handlers = defaultdict(list)
        for state_meta in self.handlers:
            model = self.create_handler(state_meta, handler_context=self.context)
            handlers[self.workflow_state.uid].append(model)
        return handlers

    def create_handler(self, metadata, handler_context):
        return self.model(
            state_uid=self.workflow_state.uid,
            metadata=metadata,
            context=handler_context,
        )


if __name__ == "__main__":
    pass
