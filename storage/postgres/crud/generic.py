from typing import Generic, TypeVar, Type, Optional, List, Dict, Any, Union
from sqlalchemy import select, update as sa_update, delete as sa_delete
from pydantic import BaseModel
from ..base import EFSDatabase


ModelType = TypeVar("ModelType")  # ORM model type


class CRUDBase(Generic[ModelType]):
    """
    Generic CRUD operations for SQLAlchemy ORM models (async).
    - M: ORM model class (declarative)
    - CreateSchemaType / UpdateSchemaType: Pydantic models for input
    """

    def __init__(self, model: Type[M]):
        """
        model: SQLAlchemy declarative model class
        """
        self.model = model
        self.context = EFSDatabase()

    async def get(self, id: Any) -> Optional[ModelType]:
        async with self.context.session as session:
            stmt = select(self.model).where(self.model.id == id)
            res = await session.execute(stmt)
            return res.scalars().first()

    async def get_all(self, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        async with self.context.session as session:
            stmt = select(self.model).offset(skip).limit(limit)
            res = await session.execute(stmt)
            return res.scalars().all()

    async def get_by(self, **kwargs) -> Optional[ModelType]:
        """
        Get first object matching kwargs: e.g. get_by(db, email="a@b")
        """
        async with self.context.session as session:
            stmt = select(self.model).filter_by(**kwargs).limit(1)
            res = await session.execute(stmt)
            return res.scalars().first()

    async def update(self, id: Any, obj_in: Dict[str, Any]) -> Optional[ModelType]:
        async with self.context.session as session:
            stmt = select(self.model).where(self.model.id == id)
            res = await session.execute(stmt)
            obj = res.scalars().first()
            if not obj:
                return None
            for field, value in obj_in.items():
                setattr(obj, field, value)
            await session.commit()
            await session.refresh(obj)
            return obj
