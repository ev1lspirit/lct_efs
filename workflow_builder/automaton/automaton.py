from operator import attrgetter
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel

if TYPE_CHECKING:
    from ..states import WorkflowState

class Automaton:

    def __init__(self, states: list['WorkflowState']):
        self.states = states
        self.current_state: Optional['WorkflowState'] = None

    def __iter__(self):
        self.current_state = next(filter(attrgetter("initial_state"), self.states))
        return self

    def __next__(self):
        current_state: WorkflowState = self.current_state
        if current_state is None:
            print("No current state")
            return None

        for expr in current_state.executables:
            result = expr.result()
            executable_transition = expr.metadata.transition_bind_object
            executable_case = eval(executable_transition.case)
            print(f"Evaluating expression for transition '{executable_case}': {result}")
            if result == executable_case:
                print(f"Found matched transition: {executable_transition}")
                return executable_transition
        raise ValueError("No matching transition found")

    @classmethod
    def from_workflow_description(cls, workflow_description: BaseModel):
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__} states={self.states}>"
