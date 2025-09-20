from abc import ABC
import inspect
from typing import Any, NoReturn
from .schema import State


class ValidatorDescriptor:

    def __init__(self):
        self.fsm: list[State] = None

    def __set__(self, *args, **kwds) -> NoReturn:
        raise AttributeError("Can't set attribute")

    def __get__(self, instance, cls_) -> list[State]:
        if self.fsm is None:
            self.fsm = getattr(instance, "fsm")
        return self.fsm


class FSMAbstractValidator(ValidatorDescriptor, ABC):
    """Класс абстрактного валидатора, применяет валидаторы на автомат"""

    def __get_validators(self) -> list[Any]:
        is_validator = lambda pair: all([
            not pair[0].startswith("__"), inspect.ismethod(pair[1])
        ])
        return [validator for _, validator
                in filter(is_validator,
                          vars(self.__class__).items())
        ]

    def apply_validators(self) -> bool:
        validators = self.__get_validators()
        for validator in validators:
            validation_result = validator(self.fsm)
            if validation_result is False:
                raise ValueError(f"Validator {validator.__name__} returned false for state list.")
        return True
