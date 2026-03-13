import typing

from sqlalchemy import BigInteger, Column, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship

from app.backend.store.database.sqlalchemy_base import BaseModel

if typing.TYPE_CHECKING:
    from app.backend.game.models import GameUserModel


class UserModel(BaseModel):
    __tablename__ = "user"
    __table_args__ = (UniqueConstraint("tg_id", name="uq_user_tg_id"),)

    user_id = Column(BigInteger, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, nullable=False)
    max_balance = Column(Numeric(12, 2), default=1000.0, nullable=False)
    games_played = Column(Integer, default=0, nullable=False)
    games_won = Column(Integer, default=0, nullable=False)

    game_users: list["GameUserModel"] = relationship(
        "GameUserModel", back_populates="user"
    )
