from pydantic import BaseModel

from workflow_builder.models import StateTypeEnum


class StateMetadata(BaseModel):
    name: str
    type_: StateTypeEnum
