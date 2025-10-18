from workflow_builder.state_parser.contract import StateSet
from pydantic import BaseModel
from typing import Any, Optional, Union


class SaveWorkflowRequest(BaseModel):
    states: StateSet
    predefined_context: dict[str, Any] = {}


class WorkflowRequest(BaseModel):
    client_session_id: str
    client_workflow_id: Optional[str] = None
    context: dict[str, Union[str, int, list, dict]] = {}
    event_name: Optional[str] = None
