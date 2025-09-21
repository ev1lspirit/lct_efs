from typing import TypeVar
import uuid
from dataclasses import dataclass, field as dfield
from uuid import UUID


StateModel = TypeVar("StateModel")

@dataclass
class WorkflowState:
    id: UUID = dfield(default=uuid.uuid4())
