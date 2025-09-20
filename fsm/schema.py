from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field


# ---------- Условия ----------
class ConditionItem(BaseModel):
    var: Optional[str] = None
    operator: Optional[str] = None
    argument: Optional[Union[str, int, float, List[Any]]] = None
    nextItemRelation: Optional[str] = Field(default="and")  # по умолчанию and
    between: Optional[List[Any]] = None  # для диапазонов


class UserConditions(BaseModel):
    condition_name: str
    conditionGroup: List[ConditionItem]


# ---------- MatchConditions в переходах ----------

class ValidatorMatchCondition(BaseModel):
    validator: Optional[str] = None
    invert: Optional[bool] = None
    kwargs: Optional[Dict[str, Any]] = None

class VariableMatchCondition(BaseModel):
    var: Optional[str] = None
    operator: Optional[str] = None
    argument: Optional[Union[str, int, float, List[Any]]] = None

class BetweenMatchCondition:
    var: Optional[str] = None
    between: Optional[List[Any]] = None

MatchCondtion = Union[
    ValidatorMatchCondition, VariableMatchCondition, BetweenMatchCondition
]

# ---------- Переходы ----------
class Transition(BaseModel):
    destination: str
    matchConditions: Optional[List[MatchCondtion]] = None


# ---------- Состояния ----------
class State(BaseModel):
    name: str
    type: str  # "Internal" | "Transaction" | "Screen"
    transitions: Optional[List[Transition]] = None
    final: Optional[bool] = False


# ---------- Основная структура ----------
class DataModel(BaseModel):
    context: str
    userConditions: List[UserConditions]
    state_set: List[State]


class Contract(BaseModel):
    data: DataModel
