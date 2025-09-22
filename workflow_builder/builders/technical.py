from .base import BaseHandlersCreator
from ..handlers import TechnicalHandler


class WorkflowTechnicalHandlersCreator(BaseHandlersCreator[TechnicalHandler]):

    def __call__(self):
        handlers = []
        for state_meta in self.handlers:
            model = self.create_handler(state_meta, handler_context=self.context)
            handlers.append(model)
        return handlers



if __name__ == "__main__":
    pass
