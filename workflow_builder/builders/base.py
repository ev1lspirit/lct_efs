from context import SessionContext
from ..handlers import HandlerClass, HandlerMeta
from attr import define, field
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar, Generic, get_args

if TYPE_CHECKING:
    from ..states import WorkflowState


@define
class BaseHandlersCreator(Generic[HandlerClass], ABC):
    workflow_state: 'WorkflowState' = field()
    handlers: list[HandlerMeta] = field()
    context: ClassVar[SessionContext] = SessionContext()

    def __init_subclass__(cls, **kwargs) -> None:
        """Инициализирует аттрибут :attr:`model` значением из тип-параметра генерика"""
        super().__init_subclass__(**kwargs)
        cls.model = get_args(cls.__orig_bases__[0])[0]  # type: ignore[attr-defined]

    @abstractmethod
    def __call__(self) -> Any: ...

    @abstractmethod
    def create_handler(self, metadata, handler_context): ...
