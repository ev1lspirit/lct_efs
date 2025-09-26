from attrs import define

@define(slots=True)
class Transition:
    case: str  # condition to evaluate
    state_id: str  # target state id
