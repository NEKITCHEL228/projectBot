import typing

from sqlalchemy import BigInteger, Column, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.backend.store.database.sqlalchemy_base import BaseModel

if typing.TYPE_CHECKING:
    from app.backend.game.models import GameUserModel


class UserModel(BaseModel):
    __tablename__ = "app_user"
    __allow_unmapped__ = True
    
    __table_args__ = (UniqueConstraint("tg_id", name="uq_user_tg_id"),)

    user_id = Column(BigInteger, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, nullable=False)
    name = Column(String(255), nullable=False, default="")
    max_balance = Column(Numeric(12, 2), default=1000.0, nullable=False)
    games_played = Column(Integer, default=0, nullable=False)
    games_won = Column(Integer, default=0, nullable=False)

    game_user: list["GameUserModel"] = relationship(
        "GameUserModel", back_populates="user"
    )
