from fastapi import APIRouter
from fastapi.responses import JSONResponse

from workflow_builder.state_parser.contract import StateModel

router = APIRouter()

@router.post("/states/")
async def create_states(states: list[StateModel]):
    # здесь можно делать что угодно: сохранять в БД, проверять логические связи и т.д.
    pass
