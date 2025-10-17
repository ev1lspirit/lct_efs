from collections.abc import Callable
import inspect
import logging


logger = logging.getLogger(__name__)

class AssertCallerMixin:

    @staticmethod
    def __get_methods(class_):
        return {
            name: method
            for name, method in inspect.getmembers(
                class_, predicate=inspect.isfunction
            )
            if name.startswith("_assert")
        }

    def apply_assert(self):
        child_methods = self.__get_methods(self.__class__)
        for name, method in child_methods.items():
            if callable(method):
                print(f"Calling asserter: {name}")
                method(self)
