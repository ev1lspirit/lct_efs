from ..states import WorkflowState
from .base import BaseHandlersCreator
from ..handlers import HandlerMeta, TechnicalHandler
from collections import defaultdict


class WorkflowTechnicalHandlersCreator(BaseHandlersCreator[TechnicalHandler]):

    def __call__(self):
        handlers = defaultdict(list)
        for state_meta in self.handlers:
            full_state_context = set(state_meta.dependent_variables) | {
                state_meta.variable
            }
            local_context = set(self.context.keys()) & full_state_context
            model = self.model(
                state_uid=self.workflow_state.id,
                metadata=state_meta,
                context={key: self.context[key] for key in local_context},
            )
            handlers[self.workflow_state.id].append(model)
        return handlers


if __name__ == "__main__":
    obj = WorkflowTechnicalHandlersCreator(
        workflow_state=WorkflowState(),  # тут объект воркфлоу
        context={"x": None, "z": 1, "y": 7, "l": 4},
        handlers=[
            HandlerMeta(
                variable="x",
                dependent_variables=["z", "y"],
                execution_context="z*2-y",
            )
        ],
    )
    meta = obj()

    for state_id, handlers in meta.items():
        for handler in handlers:
            print(handler.result)
