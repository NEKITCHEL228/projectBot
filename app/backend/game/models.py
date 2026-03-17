import typing
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    BigInteger,
    Boolean
)
from sqlalchemy.orm import relationship

from app.backend.store.database.sqlalchemy_base import BaseModel

if typing.TYPE_CHECKING:
    from app.backend.user.models import UserModel


class GameStatusEnum(str, PyEnum):
    WAITING_FOR_PLAYERS = "waiting_for_players"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


class GameModel(BaseModel):
    __tablename__ = "game"
    __allow_unmapped__ = True
    
    __table_args__ = (
        Index("ix_game_chat_id", "chat_id"),
        Index("ix_game_created_at", "created_at"),
    )

    game_id = Column(BigInteger, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    game_status = Column(Enum(GameStatusEnum), nullable=False)
    game_trading_session_round = Column(Integer, default=1, nullable=False)
    max_rounds = Column(Integer, nullable=False)

    game_user: list["GameUserModel"] = relationship(
        "GameUserModel",
        back_populates="game",
        cascade="all, delete-orphan",
    )
    company_shares: list["CompanySharesModel"] = relationship(
        "CompanySharesModel",
        back_populates="game",
        cascade="all, delete-orphan",
    )
    game_state: "GameStateModel" = relationship(
        "GameStateModel",
        back_populates="game",
        uselist=False,
        cascade="all, delete-orphan",
    )


class GameUserModel(BaseModel):
    __tablename__ = "game_user"
    __allow_unmapped__ = True
    
    __table_args__ = (
        UniqueConstraint("game_id", "user_id", name="uq_game_user"),
        Index("ix_game_user_game_id", "game_id"),
        Index("ix_game_user_user_id", "user_id"),
    )

    game_user_id = Column(BigInteger, primary_key=True, autoincrement=True)
    game_id = Column(BigInteger, ForeignKey("game.game_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=False)

    game: "GameModel" = relationship("GameModel", back_populates="game_user")
    user: "UserModel" = relationship("UserModel", back_populates="game_user")
    balance: "UserBalanceModel" = relationship(
        "UserBalanceModel",
        back_populates="game_user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    company_shares: list["UserCompanyShareModel"] = relationship(
        "UserCompanyShareModel",
        back_populates="game_user",
        cascade="all, delete-orphan",
    )
    turn_state: "PlayerTurnStateModel" = relationship(
        "PlayerTurnStateModel",
        back_populates="game_user",
        uselist=False,
        cascade="all, delete-orphan",
    )


class GameStateModel(BaseModel):
    __tablename__ = "game_state"
    __allow_unmapped__ = True

    game_state_id = Column(BigInteger, primary_key=True, autoincrement=True)
    game_id = Column(
        BigInteger, ForeignKey("game.game_id", ondelete="CASCADE"),
        nullable=False, unique=True
    )
    lobby_message_id   = Column(BigInteger, nullable=True)
    confirm_message_id = Column(BigInteger, nullable=True)

    game: "GameModel" = relationship("GameModel", back_populates="game_state")
    
    
class PlayerTurnStateModel(BaseModel):
    __tablename__ = "player_turn_state"
    __allow_unmapped__ = True

    player_turn_state_id = Column(BigInteger, primary_key=True, autoincrement=True)
    game_user_id = Column(
        BigInteger, ForeignKey("game_user.game_user_id", ondelete="CASCADE"),
        nullable=False, unique=True
    )
    turn_ended     = Column(Boolean, default=False, nullable=False)
    pending_action = Column(String(32), nullable=True)

    game_user: "GameUserModel" = relationship("GameUserModel", back_populates="turn_state")

class CompanySharesModel(BaseModel):
    __tablename__ = "company_shares"
    __allow_unmapped__ = True
    
    __table_args__ = (
        UniqueConstraint("game_id", "company_share_name", name="uq_company_share_game_name"),
        Index("ix_company_shares_game_id", "game_id"),
    )

    company_share_id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(BigInteger, ForeignKey("game.game_id", ondelete="CASCADE"), nullable=False)
    company_share_name = Column(String, nullable=False)
    company_share_price = Column(Numeric(12, 2), nullable=False)

    game: "GameModel" = relationship("GameModel", back_populates="company_shares")
    user_shares: list["UserCompanyShareModel"] = relationship(
        "UserCompanyShareModel", back_populates="company_share"
    )


class UserCompanyShareModel(BaseModel):
    __tablename__ = "user_company_share"
    __allow_unmapped__ = True
    
    __table_args__ = (
        UniqueConstraint(
            "game_user_id", "company_share_id", name="uq_user_company_share"
        ),
    )

    user_company_share_id = Column(Integer, primary_key=True, autoincrement=True)
    game_user_id = Column(
        BigInteger, ForeignKey("game_user.game_user_id", ondelete="CASCADE"), nullable=False
    )
    company_share_id = Column(
        BigInteger, ForeignKey("company_shares.company_share_id"), nullable=False
    )
    company_share_count = Column(Integer, default=0, nullable=False)

    game_user: "GameUserModel" = relationship(
        "GameUserModel", back_populates="company_shares"
    )
    company_share: "CompanySharesModel" = relationship(
        "CompanySharesModel", back_populates="user_shares"
    )


class UserBalanceModel(BaseModel):
    __tablename__ = "user_balance"
    __allow_unmapped__ = True

    user_balance_id = Column(Integer, primary_key=True, autoincrement=True)
    game_user_id = Column(
        BigInteger,
        ForeignKey("game_user.game_user_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    full_balance = Column(Numeric(12, 2), default=1000.0, nullable=False)
    pure_balance = Column(Numeric(12, 2), default=1000.0, nullable=False)
    company_share_balance = Column(Numeric(12, 2), default=0.0, nullable=False)

    game_user: "GameUserModel" = relationship(
        "GameUserModel", back_populates="balance"
    )
