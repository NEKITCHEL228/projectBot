import asyncio
from typing import TYPE_CHECKING
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.backend.base.base_accessor import BaseAccessor
from app.backend.game.models import (
    GameModel,
    GameUserModel,
    GameStatusEnum,
)
if TYPE_CHECKING:
    from app.backend.web.app import Application

class GameAccessor(BaseAccessor):
    def __init__(self, app: "Application"):
        self.app = app
    
    async def get_active_game(self, chat_id: int) -> GameModel | None:
        """Возвращает активную игру (waiting_for_players или in_progress) с загруженными игроками."""
        query = (
            select(GameModel)
            .where(
                GameModel.chat_id == chat_id,
                GameModel.game_status.in_([
                    GameStatusEnum.WAITING_FOR_PLAYERS,
                    GameStatusEnum.IN_PROGRESS,
                ]),
            )
            .options(
                selectinload(GameModel.game_user).selectinload(GameUserModel.user)
            )
        )
        async with self.app.database.session() as session:
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def create_game(self, chat_id: int) -> GameModel:
        """Создаёт игру со статусом waiting_for_players."""
        game = GameModel(
            chat_id=chat_id,
            game_status=GameStatusEnum.WAITING_FOR_PLAYERS,
            max_rounds=10,
        )
        async with self.app.database.session() as session:
            session.add(game)
            await session.commit()
            await session.refresh(game)
        return game

    async def add_player_to_game(self, game_id: int, user_id: int) -> bool:
        """Добавляет игрока в игру. Возвращает False если игрок уже в игре."""
        check = select(GameUserModel).where(
            GameUserModel.game_id == game_id,
            GameUserModel.user_id == user_id,
        )
        async with self.app.database.session() as session:
            result = await session.execute(check)
            if result.scalar_one_or_none():
                return False
            session.add(GameUserModel(game_id=game_id, user_id=user_id))
            await session.commit()
        return True

    async def start_game(self, game_id: int) -> None:
        """Переводит игру в статус in_progress."""
        query = select(GameModel).where(GameModel.game_id == game_id)
        async with self.app.database.session() as session:
            result = await session.execute(query)
            game = result.scalar_one_or_none()
            if game:
                game.game_status = GameStatusEnum.IN_PROGRESS
                await session.commit()

    async def finish_game(self, game_id: int) -> None:
        """Переводит игру в статус finished."""
        query = select(GameModel).where(GameModel.game_id == game_id)
        async with self.app.database.session() as session:
            result = await session.execute(query)
            game = result.scalar_one_or_none()
            if game:
                game.game_status = GameStatusEnum.FINISHED
                await session.commit()

    async def remove_player_from_game(self, game_id: int, user_id: int) -> bool:
        """Удаляет игрока из лобби. Возвращает False если игрок не был в игре."""
        from sqlalchemy import delete
        query = delete(GameUserModel).where(
            GameUserModel.game_id == game_id,
            GameUserModel.user_id == user_id,
        )
        async with self.app.database.session() as session:
            result = await session.execute(query)
            await session.commit()
            return result.rowcount > 0
        
    async def get_players(self, game_id):
        query = select(GameUserModel.user).where(GameUserModel.game_id==game_id).options(selectinload(GameUserModel.user))
        
        async with self.app.database.session() as session:
            players_list = await session.execute(query)
            return players_list.scalars().all()
    
    async def finish_round(self, chat_id: int, game_id: int):
        # отменяем таймер
        task = self.app.store.bots_manager.end_turn_tasks.pop(chat_id, None)
        if task:
            task.cancel()

        # сбрасываем голоса
        self.app.store.bots_manager.end_turn_votes.pop(chat_id, None)

        await self.app.store.tg_api.send_message(
            chat_id,
        "⏳ Раунд завершён. Переход к следующему..."
        )
    
    async def _end_turn_timeout(self, chat_id: int, game_id: int):
        await asyncio.sleep(30)
        await self.finish_round(chat_id, game_id)
