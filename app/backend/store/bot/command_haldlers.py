from typing import TYPE_CHECKING

from app.backend.store.bot.callbacks import (
    StartGameCallback,
    JoinGameCallback,
    EndGameCallback,
    ContinueGameCallback,
)
from app.backend.store.bot.router import BotRouter
from app.backend.store.tg_api.game_constraints import (
    MainMenuButtons,
    BotCommands,
    GameButtons,
    GameCommands,
)
from app.backend.store.tg_api.game_builders import (
    MAIN_MENU_BUTTONS,
    MAIN_MENU_TEXT,
    GAME_MENU_BUTTONS,
    RULES_TEXT,
    build_lobby_message,
    build_lobby_entrance_message,
    build_lobby_exit_message,
    build_game_start_text,
    build_end_game_confirm_keyboard,
    build_buy_companies_message,
    build_sell_portfolio_message,
    build_portfolio_message,
    build_stats_message,
)

if TYPE_CHECKING:
    from app.backend.store.bot.manager import BotManager

router = BotRouter()

# ── Вспомогательная функция: проверка что user_id в игре ──────────────────────

def _is_player_in_game(game, user_id_tg: int) -> bool:
    """Проверяет что tg_id есть среди игроков."""
    return any(gu.user.tg_id == user_id_tg for gu in game.game_user)

# ═══════════════════════════════════════════════════════════════════════════════
#  /start
# ═══════════════════════════════════════════════════════════════════════════════

@router.message("/start", "/start@BirzjaGameBot")
async def handle_start(self: "BotManager", chat_id: int, user_id: int):
    await self.app.store.tg_api.send_keyboard(chat_id, MAIN_MENU_TEXT, MAIN_MENU_BUTTONS)


# ═══════════════════════════════════════════════════════════════════════════════
#  Начать игру → открыть лобби
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(MainMenuButtons.start_game, BotCommands.start_game)
async def handle_start_game(self: "BotManager", chat_id: int, user_id: int):
    game = await self.app.store.games.get_active_game(chat_id)

    if game and game.game_status.value == "in_progress":
        await self.app.store.tg_api.send_message(chat_id, "Игра уже идёт в этом чате, дождитесь её окончания.")
        return

    if game and game.game_status.value == "waiting_for_players":
        await self.app.store.tg_api.send_message(chat_id, "Лобби уже открыто! Нажмите «Присоединиться» в сообщении лобби.")
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


# ═══════════════════════════════════════════════════════════════════════════════
#  Inline: Присоединиться к игре
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback(JoinGameCallback)
async def handle_join_game_callback(
    self: "BotManager", chat_id: int, user_id: int, callback: JoinGameCallback
):
    game = await self.app.store.games.get_active_game(chat_id)

    if not game or game.game_status.value != "waiting_for_players":
        await self.app.store.tg_api.send_message(chat_id, "Лобби уже закрыто.")
        return

    user = await self.app.store.users.get_by_tg_id(user_id)
    if not user:
        await self.app.store.tg_api.send_message(chat_id, "Сначала введите /start для регистрации.")
        return

    added = await self.app.store.games.add_player_to_game(game.game_id, user.user_id)
    if not added:
        await self.app.store.tg_api.send_message(chat_id, f"{user.name}, вы уже в лобби!")
        return

    # Обновляем inline-сообщение лобби
    updated_game = await self.app.store.games.get_active_game(chat_id)
    user_names = [gu.user.name for gu in updated_game.game_user]
    text, keyboard = build_lobby_message(user_names, game.game_id)

    old_message_id = self.lobby_message_ids.pop(chat_id, None)
    if old_message_id:
        await self.app.store.tg_api.delete_message(chat_id, old_message_id)

    message_id = await self.app.store.tg_api.send_inline_keyboard(chat_id, text, keyboard)
    if message_id:
        self.lobby_message_ids[chat_id] = message_id

    entrance_message = build_lobby_entrance_message(user, game.game_id)
    await self.app.store.tg_api.send_message(chat_id, entrance_message)

# ═══════════════════════════════════════════════════════════════════════════════
#  Inline: Начать игру (из лобби)
# ═══════════════════════════════════════════════════════════════════════════════

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

    # Удаляем сообщение лобби
    lobby_message_id = self.lobby_message_ids.pop(chat_id, None)
    if lobby_message_id:
        await self.app.store.tg_api.delete_message(chat_id, lobby_message_id)

    await self.app.store.games.start_game(callback.game_id)

    user_names = [gu.user.name for gu in game.game_user]
    start_text = build_game_start_text(user_names, callback.game_id)

    # Отправляем reply-клавиатуру с кнопками покупки/продажи/портфеля
    await self.app.store.tg_api.send_keyboard(chat_id, start_text, GAME_MENU_BUTTONS)
    # Отправляем сообщение о 1 раунде
    await self.app.store.games.print_round_message(callback.game_id)

# ═══════════════════════════════════════════════════════════════════════════════
#  Покинуть игру (главное меню — только из лобби)
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(MainMenuButtons.leave_game, BotCommands.leave_game)
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

    exit_message = build_lobby_exit_message(user, game.game_id)

    if not remaining:
        await self.app.store.games.finish_game(game.game_id)
        await self.app.store.tg_api.send_keyboard(
            chat_id,
            exit_message + "\nЛобби закрыто — все игроки вышли.",
            MAIN_MENU_BUTTONS,
        )
        return

    user_names = [gu.user.name for gu in remaining]
    text, keyboard = build_lobby_message(user_names, game.game_id)
    message_id = await self.app.store.tg_api.send_inline_keyboard(chat_id, text, keyboard)
    if message_id:
        self.lobby_message_ids[chat_id] = message_id

    await self.app.store.tg_api.send_message(chat_id, exit_message)


# ═══════════════════════════════════════════════════════════════════════════════
#  Статистика и правила
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(MainMenuButtons.show_stats, BotCommands.show_stats)
async def handle_show_stats(self: "BotManager", chat_id: int, user_id: int):
    user = await self.app.store.users.get_by_tg_id(user_id)
    if not user:
        await self.app.store.tg_api.send_message(
            chat_id, "Пользователь не найден. Введите /start для регистрации."
        )
        return
    await self.app.store.tg_api.send_message(chat_id, build_stats_message(user))


@router.message(MainMenuButtons.show_rules, BotCommands.show_rules)
async def handle_show_rules(self: "BotManager", chat_id: int, user_id: int):
    await self.app.store.tg_api.send_message(chat_id, RULES_TEXT)

# ═══════════════════════════════════════════════════════════════════════════════
#  Купить Акции (кнопка) — показываем список акций с командами
# ═══════════════════════════════════════════════════════════════════════════════
 
@router.message(GameButtons.buy_shares, GameCommands.buy_shares)
async def handle_buy_shares(self: "BotManager", chat_id: int, user_id: int):
    game = await self.app.store.games.get_active_game(chat_id)
    if not game or game.game_status.value != "in_progress":
        return
 
    if not _is_player_in_game(game, user_id):
        await self.app.store.tg_api.send_message(chat_id, "❌ Вы не участвуете в этой игре.")
        return
 
    if self.has_ended_turn(chat_id, user_id):
        await self.app.store.tg_api.send_message(
            chat_id, "❌ Вы завершили ход и не можете покупать акции в этом раунде."
        )
        return
 
    user = await self.app.store.users.get_by_tg_id(user_id)
    portfolio, balance = await self.app.store.games.get_portfolio(game.game_id, user.user_id)
    companies = await self.app.store.games.get_companies(game.game_id)
 
    await self.app.store.tg_api.send_message(
        chat_id, build_buy_companies_message(companies, balance)
    )
 
# ═══════════════════════════════════════════════════════════════════════════════
#  Продать Акции (кнопка) — показываем портфель с командами продажи
# ═══════════════════════════════════════════════════════════════════════════════
 
@router.message(GameButtons.sell_shares, GameCommands.sell_shares)
async def handle_sell_shares(self: "BotManager", chat_id: int, user_id: int):
    game = await self.app.store.games.get_active_game(chat_id)
    if not game or game.game_status.value != "in_progress":
        return
 
    if not _is_player_in_game(game, user_id):
        await self.app.store.tg_api.send_message(chat_id, "❌ Вы не участвуете в этой игре.")
        return
 
    if self.has_ended_turn(chat_id, user_id):
        await self.app.store.tg_api.send_message(
            chat_id, "❌ Вы завершили ход и не можете продавать акции в этом раунде."
        )
        return
 
    user = await self.app.store.users.get_by_tg_id(user_id)
    portfolio, balance = await self.app.store.games.get_portfolio(game.game_id, user.user_id)
 
    await self.app.store.tg_api.send_message(
        chat_id, build_sell_portfolio_message(portfolio, balance)
    )

# ═══════════════════════════════════════════════════════════════════════════════
#  /buy НАЗВАНИЕ КОЛИЧЕСТВО — выполнить покупку
# ═══════════════════════════════════════════════════════════════════════════════
 
@router.command(GameCommands.buy)
async def handle_buy_command(self: "BotManager", chat_id: int, user_id: int, text: str):
    game = await self.app.store.games.get_active_game(chat_id)
    if not game or game.game_status.value != "in_progress":
        return
 
    if not _is_player_in_game(game, user_id):
        await self.app.store.tg_api.send_message(chat_id, "❌ Вы не участвуете в этой игре.")
        return
 
    if self.has_ended_turn(chat_id, user_id):
        await self.app.store.tg_api.send_message(
            chat_id, "❌ Вы завершили ход и не можете покупать акции в этом раунде."
        )
        return
 
    # Парсим: /buy TELEGRAM 5
    parts = text.strip().split()
    if len(parts) != 3:
        await self.app.store.tg_api.send_message(
            chat_id, "⚠️ Формат: `/buy НАЗВАНИЕ КОЛИЧЕСТВО`\nНапример: `/buy TELEGRAM 5`"
        )
        return
 
    _, company_name, qty_str = parts
    if not qty_str.isdigit() or int(qty_str) <= 0:
        await self.app.store.tg_api.send_message(chat_id, "⚠️ Количество должно быть положительным числом.")
        return
 
    user = await self.app.store.users.get_by_tg_id(user_id)
    if not user:
        return
 
    success, message = await self.app.store.games.buy_shares(
        game.game_id, user.user_id, company_name.upper(), int(qty_str)
    )
    await self.app.store.tg_api.send_message(chat_id, message)
 
# ═══════════════════════════════════════════════════════════════════════════════
#  /sell НАЗВАНИЕ КОЛИЧЕСТВО — выполнить продажу
# ═══════════════════════════════════════════════════════════════════════════════
 
@router.command(GameCommands.sell)
async def handle_sell_command(self: "BotManager", chat_id: int, user_id: int, text: str):
    game = await self.app.store.games.get_active_game(chat_id)
    if not game or game.game_status.value != "in_progress":
        return
 
    if not _is_player_in_game(game, user_id):
        await self.app.store.tg_api.send_message(chat_id, "❌ Вы не участвуете в этой игре.")
        return
 
    if self.has_ended_turn(chat_id, user_id):
        await self.app.store.tg_api.send_message(
            chat_id, "❌ Вы завершили ход и не можете продавать акции в этом раунде."
        )
        return
 
    # Парсим: /sell TELEGRAM 3
    parts = text.strip().split()
    if len(parts) != 3:
        await self.app.store.tg_api.send_message(
            chat_id, "⚠️ Формат: `/sell НАЗВАНИЕ КОЛИЧЕСТВО`\nНапример: `/sell TELEGRAM 3`"
        )
        return
 
    _, company_name, qty_str = parts
    if not qty_str.isdigit() or int(qty_str) <= 0:
        await self.app.store.tg_api.send_message(chat_id, "⚠️ Количество должно быть положительным числом.")
        return
 
    user = await self.app.store.users.get_by_tg_id(user_id)
    if not user:
        return
 
    success, message = await self.app.store.games.sell_shares(
        game.game_id, user.user_id, company_name.upper(), int(qty_str)
    )
    await self.app.store.tg_api.send_message(chat_id, message)

# ═══════════════════════════════════════════════════════════════════════════════
#  Просмотреть портфель
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(GameButtons.show_portfolio, GameCommands.show_portfolio)
async def handle_show_portfolio(self: "BotManager", chat_id: int, user_id: int):
    game = await self.app.store.games.get_active_game(chat_id)
    if not game or game.game_status.value != "in_progress":
        return

    user = await self.app.store.users.get_by_tg_id(user_id)
    if not user:
        return

    portfolio, balance = await self.app.store.games.get_portfolio(game.game_id, user.user_id)
    await self.app.store.tg_api.send_message(
        chat_id, build_portfolio_message(user, portfolio, balance)
    )

# ═══════════════════════════════════════════════════════════════════════════════
#  Завершить Ход (reply-кнопка)
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(GameButtons.end_turn, GameCommands.end_turn)
async def handle_end_turn(self: "BotManager", chat_id: int, user_id: int):
    game = await self.app.store.games.get_active_game(chat_id)
    if not game or game.game_status.value != "in_progress":
        return

    # Проверяем что игрок участвует в игре
    if not _is_player_in_game(game, user_id):
        await self.app.store.tg_api.send_message(chat_id, "❌ Вы не участвуете в этой игре.")
        return

    if self.has_ended_turn(chat_id, user_id):
        await self.app.store.tg_api.send_message(chat_id, "Вы уже завершили ход.")
        return

    self.mark_turn_ended(chat_id, user_id)
    self.clear_pending_action(chat_id, user_id)

    user = await self.app.store.users.get_by_tg_id(user_id)
    name = user.name if user else "Игрок"
    players_count = len(game.game_user)
    ended_count = len(self.ended_turns.get(chat_id, set()))

    await self.app.store.tg_api.send_message(
        chat_id,
        f"✅ {name} завершил ход. ({ended_count}/{players_count})"
    )

    if ended_count >= players_count:
        await self.app.store.games.finish_round(chat_id, game.game_id)

# ═══════════════════════════════════════════════════════════════════════════════
#  Завершить игру (reply-кнопка) → подтверждение
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(GameButtons.end_game, GameCommands.end_game)
async def handle_end_game_request(self: "BotManager", chat_id: int, user_id: int):
    game = await self.app.store.games.get_active_game(chat_id)
    if not game or game.game_status.value != "in_progress":
        return

    # Проверяем что игрок участвует в игре
    if not _is_player_in_game(game, user_id):
        await self.app.store.tg_api.send_message(chat_id, "❌ Вы не участвуете в этой игре.")
        return

    keyboard = build_end_game_confirm_keyboard(game.game_id)
    message_id = await self.app.store.tg_api.send_inline_keyboard(
        chat_id, "❓ Вы уверены, что хотите завершить игру?", keyboard
    )
    if message_id:
        self.confirm_message_ids[chat_id] = message_id

# ═══════════════════════════════════════════════════════════════════════════════
#  Inline: Подтверждение / отмена завершения игры
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback(EndGameCallback)
async def handle_end_game_callback(
    self: "BotManager", chat_id: int, user_id: int, callback: EndGameCallback
):  
    # Удаляем сообщения о подтверждении
    confirm_id = self.confirm_message_ids.pop(chat_id, None)
    if confirm_id:
        await self.app.store.tg_api.delete_message(chat_id, confirm_id)
    
    game = await self.app.store.games.get_active_game(chat_id)
    if not game:
        await self.app.store.tg_api.send_message(chat_id, "Игра не найдена.")
        return

    self.reset_turns(chat_id)
    self._pending_actions.pop(chat_id, None) 
      
    await self.app.store.games.finish_game(callback.game_id)

@router.callback(ContinueGameCallback)
async def handle_continue_game_callback(
    self: "BotManager", chat_id: int, user_id: int, callback: ContinueGameCallback
):
    # Удаляем сообщение о подтверждении
    confirm_id = self.confirm_message_ids.pop(chat_id, None)
    if confirm_id:
        await self.app.store.tg_api.delete_message(chat_id, confirm_id)
    
    await self.app.store.tg_api.send_message(chat_id, "▶️ Игра продолжается.")