from typing import TYPE_CHECKING

from app.backend.store.bot.callbacks import StartGameCallback
from app.backend.store.bot.router import BotRouter
from app.backend.store.tg_api.game_constraints import BotCommands, MainMenuButtons
from app.backend.store.tg_api.game_builders import (
    MAIN_MENU_BUTTONS,
    MAIN_MENU_TEXT,
    build_lobby_message,
)

if TYPE_CHECKING:
    from app.backend.store.bot.manager import BotManager

router = BotRouter()


@router.message("/start", "start@BirzjaGameBot")
async def handle_start(self: "BotManager", chat_id: int, user_id: int):
    await self.app.store.tg_api.send_keyboard(chat_id, MAIN_MENU_TEXT, MAIN_MENU_BUTTONS)

@router.message(MainMenuButtons.start_game, BotCommands.start_game)
async def handle_start_game(self: "BotManager", chat_id: int, user_id: int):
    game = await self.app.store.games.get_active_game(chat_id)

    if game and game.game_status.value == "in_progress":
        await self.app.store.tg_api.send_message(chat_id, "Игра уже идёт в этом чате, дождитесь её окончания.")
        return

    if game and game.game_status.value == "waiting_for_players":
        await self.app.store.tg_api.send_message(chat_id, "Лобби уже открыто! Присоединяйтесь командой /join_game.")
        return

    new_game = await self.app.store.games.create_game(chat_id)

    user = await self.app.store.users.get_by_tg_id(user_id)
    players_tg_ids = []
    if user:
        await self.app.store.games.add_player_to_game(new_game.game_id, user.user_id)
        players_tg_ids = [user_id]

    text, keyboard = build_lobby_message(players_tg_ids, new_game.game_id)
    await self.app.store.tg_api.send_inline_keyboard(chat_id, text, keyboard)


@router.message(MainMenuButtons.join_game, BotCommands.join_game)
async def handle_join_game(self: "BotManager", chat_id: int, user_id: int):
    game = await self.app.store.games.get_active_game(chat_id)

    if not game:
        await self.app.store.tg_api.send_message(chat_id, "Нет активного лобби. Создайте игру командой /start_game.")
        return

    if game.game_status.value == "in_progress":
        await self.app.store.tg_api.send_message(chat_id, "Игра уже идёт, дождитесь следующей.")
        return

    user = await self.app.store.users.get_by_tg_id(user_id)
    if not user:
        await self.app.store.tg_api.send_message(chat_id, "Сначала введите /start для регистрации.")
        return

    added = await self.app.store.games.add_player_to_game(game.game_id, user.user_id)
    if not added:
        await self.app.store.tg_api.send_message(chat_id, "Вы уже участвуете в этой игре!")
        return

    updated_game = await self.app.store.games.get_active_game(chat_id)
    players_tg_ids = [gu.user.tg_id for gu in updated_game.game_user]
    text, keyboard = build_lobby_message(players_tg_ids, game.game_id)
    await self.app.store.tg_api.send_inline_keyboard(chat_id, text, keyboard)


@router.callback(StartGameCallback)
async def handle_start_game_callback(
    self: "BotManager", chat_id: int, user_id: int, callback: StartGameCallback
):
    game = await self.app.store.games.get_active_game(chat_id)

    if not game:
        await self.app.store.tg_api.send_message(chat_id, "Игра не найдена.")
        return

    if game.game_status.value == "in_progress":
        await self.app.store.tg_api.send_message(chat_id, "Игра уже запущена!")
        return

    if len(game.game_user) < 2:
        await self.app.store.tg_api.send_message(chat_id, "Нужно минимум 2 игрока для начала игры.")
        return

    await self.app.store.games.start_game(callback.game_id)
    await self.app.store.tg_api.send_message(chat_id, "🎮 Игра началась! Удачи всем участникам!")
