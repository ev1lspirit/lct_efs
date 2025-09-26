from context import SessionContext
from ..handlers import (
    HandlerClass,
    IntegrationStateExpression,
    TechnicalStateExpression,
)
from attr import define, field
from abc import ABC
from typing import TYPE_CHECKING, ClassVar, Generic, Union, get_args

if TYPE_CHECKING:
    from ..states import WorkflowState



@define
class BaseHandlersCreator(Generic[HandlerClass], ABC):
    """ Базовый создатель обработчиков состояний """
    workflow_state: "WorkflowState" = field()
    handlers: list[Union[TechnicalStateExpression, IntegrationStateExpression]] = (
        field()
    )
    context: ClassVar[SessionContext] = SessionContext()

    def __init_subclass__(cls, **kwargs) -> None:
        """Инициализирует аттрибут :attr:`model` значением из тип-параметра генерика"""
        super().__init_subclass__(**kwargs)
        cls.model = get_args(cls.__orig_bases__[0])[0]  # type: ignore[attr-defined]

    def __call__(self, **kwargs):
        handlers = []
        for state_meta in self.handlers:
            model = self.create_handler(state_meta, handler_context=self.context, **kwargs)
            handlers.append(model)
        return handlers

    def create_handler(self, metadata, handler_context, **kwargs):
        return self.model(metadata=metadata, context=handler_context, **kwargs)
