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

        # chat_id -> lobby inline message_id
        self.lobby_message_ids: dict[int, int] = {}

        # chat_id -> game info inline message_id
        self.game_info_message_ids: dict[int, int] = {}

        # Pending input: {chat_id: {user_id: "buy" | "sell"}}
        self._pending_actions: dict[int, dict[int, str]] = {}

        # Игроки, завершившие ход в текущем раунде: {chat_id: {user_id}}
        self.ended_turns: dict[int, set[int]] = {}
        
        # chat_id -> message_id сообщения с подтверждением (конец игры и т.п.)
        self.confirm_message_ids: dict[int, int] = {}

    # ── Pending actions API ───────────────────────────────────────────────────

    def set_pending_action(self, chat_id: int, user_id: int, action: str) -> None:
        self._pending_actions.setdefault(chat_id, {})[user_id] = action

    def get_pending_action(self, chat_id: int, user_id: int) -> str | None:
        return self._pending_actions.get(chat_id, {}).get(user_id)

    def clear_pending_action(self, chat_id: int, user_id: int) -> None:
        chat_pending = self._pending_actions.get(chat_id, {})
        chat_pending.pop(user_id, None)

    # ── Ended turns API ───────────────────────────────────────────────────────

    def mark_turn_ended(self, chat_id: int, user_id: int) -> None:
        self.ended_turns.setdefault(chat_id, set()).add(user_id)

    def has_ended_turn(self, chat_id: int, user_id: int) -> bool:
        return user_id in self.ended_turns.get(chat_id, set())

    def reset_turns(self, chat_id: int) -> None:
        self.ended_turns.pop(chat_id, None)

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