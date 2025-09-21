from typing import Any, Type


def field_typechecker(type_: Type[Any]):

    def inner_handler(instance, attribute, value):
        if not isinstance(value, type_):
            raise TypeError(
                f"Expected type {type_.__name__} for {instance.__class__.__name__}.{attribute.name}, got {type(value).__name__}"
            )

    return inner_handler
