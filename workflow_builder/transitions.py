from attrs import define, field, validators

@define(slots=True)
class Transition:
    case: str = field(validator=validators.instance_of(str))  # condition to evaluate
    state_id: str = field(validator=validators.instance_of(str))  # target state id
    variable: str = field(default=None, validator=validators.instance_of((str, type(None)))) # type: ignore
