import typing

from sqlalchemy import (
    Column,
    String,
    UniqueConstraint,
    BigInteger
)
from sqlalchemy.orm import relationship

from app.backend.store.database.sqlalchemy_base import BaseModel

if typing.TYPE_CHECKING:
    from app.backend.user.models import UserModel


class AdminModel(BaseModel):
    __tablename__ = "admin"
    __table_args__ = (
        UniqueConstraint("tg_id", name="uq_admin_tg_id"),
    )

    admin_id = Column(BigInteger, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, nullable=False)
    password_hash = Column(String(64), nullable=False)
