from datetime import datetime
from typing import Any
from sqlalchemy import TIMESTAMP, BigInteger, func
from sqlalchemy.orm import declarative_base, Mapped, mapped_column


Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True

    pk: Mapped[int] = mapped_column(__type_pos=BigInteger, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(__type_pos=TIMESTAMP, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(__type_pos=TIMESTAMP, onupdate=func.now(), server_default=func.now())
