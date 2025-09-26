from attrs import define

@define
class Transition:
    case: str  # condition to evaluate
    state_id: str  # target state id

