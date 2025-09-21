from utils import field_typechecker
from ..handlers import HandlerClass, HandlerMeta
from ..states import WorkflowState
from attr import define, field
from abc import ABC, abstractmethod
from typing import Any, Generic, get_args


@define
class BaseHandlersCreator(Generic[HandlerClass], ABC):
    workflow_state: WorkflowState = field(
        validator=field_typechecker(type_=WorkflowState)
    )
    context: dict[str, Any] = field()
    handlers: list[HandlerMeta] = field()

    def __init_subclass__(cls, **kwargs) -> None:
        """Инициализирует аттрибут :attr:`model` значением из тип-параметра генерика"""
        super().__init_subclass__(**kwargs)
        cls.model = get_args(cls.__orig_bases__[0])[0]  # type: ignore[attr-defined]

    @abstractmethod
    def __call__(self) -> Any: ...
