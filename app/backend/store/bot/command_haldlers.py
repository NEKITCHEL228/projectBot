import asyncio
from typing import TYPE_CHECKING

from app.backend.store.bot.callbacks import ContinueGameCallback, EndGameCallback, EndTurnVoteCallback, StartGameCallback
from app.backend.store.bot.router import BotRouter
from app.backend.store.tg_api.game_constraints import LobbyButtons, BotCommands, MainMenuButtons, GameButtons, GameCommands
from app.backend.store.tg_api.game_builders import (
    MAIN_MENU_BUTTONS,
    MAIN_MENU_TEXT,
    GAME_MENU_BUTTONS,
    GAME_MENU_TEXT,
    LOBBY_BUTTONS,
    RULES_TEXT,
    build_lobby_message,
    build_stats_message,
    build_lobby_entarance_message,
    build_lobby_exit_message,
    build_game_start_text
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
    user_names = []
    if user:
        await self.app.store.games.add_player_to_game(new_game.game_id, user.user_id)
        user_names = [user.name]

    text, keyboard = build_lobby_message(user_names, new_game.game_id)
    message_id = await self.app.store.tg_api.send_inline_keyboard(chat_id, text, keyboard)
    if message_id:
        self.lobby_message_ids[chat_id] = message_id

    entrance_message = build_lobby_entarance_message(user, new_game.game_id)
    await self.app.store.tg_api.send_keyboard(chat_id, entrance_message, LOBBY_BUTTONS)


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

    old_message_id = self.lobby_message_ids.pop(chat_id, None)
    if old_message_id:
        await self.app.store.tg_api.delete_message(chat_id, old_message_id)

    updated_game = await self.app.store.games.get_active_game(chat_id)
    user_names = [gu.user.name for gu in updated_game.game_user]
    text, keyboard = build_lobby_message(user_names, game.game_id)
    message_id = await self.app.store.tg_api.send_inline_keyboard(chat_id, text, keyboard)
    if message_id:
        self.lobby_message_ids[chat_id] = message_id

    entrance_message = build_lobby_entarance_message(user, game.game_id)
    await self.app.store.tg_api.send_keyboard(chat_id, entrance_message, LOBBY_BUTTONS)


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

    lobby_message_id = self.lobby_message_ids.pop(chat_id, None)
    if lobby_message_id:
        await self.app.store.tg_api.delete_message(chat_id, lobby_message_id)

    await self.app.store.games.start_game(callback.game_id)

    user_names = [gu.user.name for gu in game.game_user]
    start_text = build_game_start_text(user_names, callback.game_id)
    await self.app.store.tg_api.send_keyboard(chat_id, start_text, GAME_MENU_BUTTONS)


@router.message(MainMenuButtons.show_stats, BotCommands.show_stats)
async def handle_show_stats(self: "BotManager", chat_id: int, user_id: int):
    user = await self.app.store.users.get_by_tg_id(user_id)
    if not user:
        await self.app.store.tg_api.send_message(chat_id, "Пользователь не найден. Зарегистрируйте пользователя командой /start.")
        return
    STATS = build_stats_message(user)
    await self.app.store.tg_api.send_message(chat_id, STATS)


@router.message(MainMenuButtons.show_rules, BotCommands.show_rules)
async def handle_show_rules(self: "BotManager", chat_id: int, user_id: int):
    await self.app.store.tg_api.send_message(chat_id, RULES_TEXT)


@router.message(LobbyButtons.leave_game, BotCommands.leave_game)
async def handle_leave_lobby(self: "BotManager", chat_id: int, user_id: int):
    game = await self.app.store.games.get_active_game(chat_id)

    if not game or game.game_status.value != "waiting_for_players":
        await self.app.store.tg_api.send_keyboard(chat_id, MAIN_MENU_TEXT, MAIN_MENU_BUTTONS)
        return

    user = await self.app.store.users.get_by_tg_id(user_id)
    if not user:
        await self.app.store.tg_api.send_message(chat_id, "Пользователь не найден.")
        return

    removed = await self.app.store.games.remove_player_from_game(game.game_id, user.user_id)
    if not removed:
        await self.app.store.tg_api.send_message(chat_id, "Вы не были в лобби.")
        return

    updated_game = await self.app.store.games.get_active_game(chat_id)
    remaining = updated_game.game_user if updated_game else []

    old_message_id = self.lobby_message_ids.pop(chat_id, None)
    if old_message_id:
        await self.app.store.tg_api.delete_message(chat_id, old_message_id)

    if not remaining:
        await self.app.store.games.finish_game(game.game_id)
        exit_message = build_lobby_exit_message(user, game.game_id)
        await self.app.store.tg_api.send_keyboard(chat_id, exit_message + "\nЛобби закрыто — все игроки вышли.", MAIN_MENU_BUTTONS)
        return

    user_names = [gu.user.name for gu in remaining]
    text, keyboard = build_lobby_message(user_names, game.game_id)
    message_id = await self.app.store.tg_api.send_inline_keyboard(chat_id, text, keyboard)
    if message_id:
        self.lobby_message_ids[chat_id] = message_id

    exit_message = build_lobby_exit_message(user, game.game_id)
    await self.app.store.tg_api.send_keyboard(chat_id, exit_message, MAIN_MENU_BUTTONS)

# Game Part
#Завершение игры
@router.message(GameButtons.end_game, GameCommands.end_game)
async def handler_end_game(self: "BotManager", chat_id: int, user_id: int):
    game = await self.app.store.games.get_active_game(chat_id)
    
    if not game or game.game_status.value != "in_progress":
        await self.app.store.tg_api.send_keyboard(chat_id, MAIN_MENU_TEXT, MAIN_MENU_BUTTONS)
        return
    
    keyboard = [[
        {"text": "Да", "callback_data": EndGameCallback.build(game_id=game.game_id)},
        {"text": "Нет", "callback_data": ContinueGameCallback.build(game_id=game.game_id)}
    ]]
    await self.app.store.tg_api.send_inline_keyboard(chat_id, "Вы уверены?", keyboard)
    
@router.callback(EndGameCallback)
async def handle_end_game_callback(
    self: "BotManager", chat_id: int, user_id: int, callback: EndGameCallback
):
    game = await self.app.store.games.get_active_game(chat_id)

    if not game:
        await self.app.store.tg_api.send_message(chat_id, "Игра не найдена.")
        return

    # завершить игру
    await self.app.store.games.finish_game(callback.game_id)

    await self.app.store.tg_api.send_keyboard(
        chat_id,
        "❌ Игра завершена.",
        MAIN_MENU_BUTTONS
    )
    
@router.callback(ContinueGameCallback)
async def handle_continue_game_callback(
    self: "BotManager", chat_id: int, user_id: int, callback: ContinueGameCallback
):
    # просто удалить сообщение с подтверждением
    await self.app.store.tg_api.delete_message(chat_id)

    await self.app.store.tg_api.send_message(chat_id, "Игра продолжается.")
    
@router.message(GameButtons.end_turn, GameCommands.end_turn)
async def handle_end_turn(self: "BotManager", chat_id: int, user_id: int):
    game = await self.app.store.games.get_active_game(chat_id)

    if not game or game.game_status.value != "in_progress":
        return

    keyboard = [[
        {"text": "Закончить ход", "callback_data": EndTurnVoteCallback.build(game_id=game.game_id)},
        {"text": "Отмена", "callback_data": ContinueGameCallback.build(game_id=game.game_id)}
    ]]

    await self.app.store.tg_api.send_inline_keyboard(
        chat_id,
        "Вы хотите закончить ход?",
        keyboard
    )
    
@router.callback(EndTurnVoteCallback)
async def handle_end_turn_vote(
    self: "BotManager", chat_id: int, user_id: int, callback: EndTurnVoteCallback
):

    game = await self.app.store.games.get_active_game(chat_id)

    if not game:
        return

    if chat_id not in self.end_turn_votes:
        self.end_turn_votes[chat_id] = set()

        # запускаем таймер
        self.end_turn_tasks[chat_id] = asyncio.create_task(
            self.app.store.games._end_turn_timeout(chat_id, callback.game_id)
        )

    votes = self.end_turn_votes[chat_id]

    if user_id in votes:
        await self.app.store.tg_api.send_message(chat_id, "Вы уже проголосовали.")
        return

    votes.add(user_id)

    players_count = len(game.game_user)

    await self.app.store.tg_api.send_message(
        chat_id,
        f"Голосов за конец хода: {len(votes)}/{players_count}"
    )

    if len(votes) >= players_count:
        await self.app.store.games.finish_round(chat_id, callback.game_id)