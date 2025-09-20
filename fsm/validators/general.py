from operator import attrgetter
from sre_parse import State
from ..base import FSMBase
from ..abstract_validator import FSMAbstractValidator


class FSMVGeneralValidator(FSMAbstractValidator):

    def has_final(self, state_list):
        final_states = list(filter(attrgetter("final"), state_list))
        return len(final_states) >= 1


class FSMValidatorEngine(FSMBase):
    validators = [FSMVGeneralValidator()]

    def __init__(self, state_list: list[State]):
        self.state_list = state_list

    def __call__(self, *args, **kwargs):
        for validator in self.validators:
            try:
                validator.apply_validators()
            except ValueError as e:
                # add logging and handling
                pass


if __name__ == "__main__":
    engine = FSMValidatorEngine([])
