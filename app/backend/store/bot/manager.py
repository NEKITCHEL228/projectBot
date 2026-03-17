import asyncio
from typing import TYPE_CHECKING
from logging import getLogger

from app.backend.store.tg_api.schemes import Update

if TYPE_CHECKING:
    from app.backend.web.app import Application
    from app.backend.store.bot.router import BotRouter


class BotManager:
    def __init__(self, app: "Application", router: "BotRouter"):
        self.app = app
        self.router = router
        self.logger = getLogger("BotManager")

    # ── GameState: lobby message ──────────────────────────────────────────────

    async def get_lobby_message_id(self, game_id: int) -> int | None:
        return await self.app.store.games.get_lobby_message_id(game_id)

    async def set_lobby_message_id(self, game_id: int, message_id: int | None) -> None:
        await self.app.store.games.set_lobby_message_id(game_id, message_id)

    # ── GameState: confirm message ────────────────────────────────────────────

    async def get_confirm_message_id(self, game_id: int) -> int | None:
        return await self.app.store.games.get_confirm_message_id(game_id)

    async def set_confirm_message_id(self, game_id: int, message_id: int | None) -> None:
        await self.app.store.games.set_confirm_message_id(game_id, message_id)

    # ── PlayerTurnState: pending actions ──────────────────────────────────────

    async def set_pending_action(self, game_id: int, user_db_id: int, action: str) -> None:
        await self.app.store.games.set_pending_action(game_id, user_db_id, action)

    async def clear_pending_action(self, game_id: int, user_db_id: int) -> None:
        await self.app.store.games.clear_pending_action(game_id, user_db_id)

    # ── PlayerTurnState: ходы ────────────────────────────────────────────────

    async def mark_turn_ended(self, game_id: int, user_db_id: int) -> None:
        await self.app.store.games.mark_turn_ended(game_id, user_db_id)

    async def has_ended_turn(self, game_id: int, user_db_id: int) -> bool:
        return await self.app.store.games.has_ended_turn(game_id, user_db_id)

    async def reset_turns(self, game_id: int) -> None:
        await self.app.store.games.reset_turns(game_id)

    # ── Обработка обновлений ──────────────────────────────────────────────────

    async def handle_updates(self, updates):
        for update in updates:
            validated = Update.model_validate(update)
            self.logger.info(f"Received update: {validated}")

            if validated.message:
                message = validated.message
                chat_id = message.chat.id
                text = message.text or ""
                user_id = message.from_user.id if message.from_user else None

                if user_id:
                    # Авто-регистрация пользователя
                    user = await self.app.store.users.get_by_tg_id(user_id)
                    if not user:
                        name = message.from_user.display_name
                        await self.app.store.users.create_user(user_id, name)

                    await self.router.route_message(self, chat_id, user_id, text)

            elif validated.callback_query:
                cb = validated.callback_query
                user_id = cb.from_user.id
                chat_id = cb.message.chat.id if cb.message else None
                data = cb.data or ""

                if chat_id and data:
                    await self.router.route_callback(self, chat_id, user_id, data)

                await self.app.store.tg_api.answer_callback_query(cb.id)