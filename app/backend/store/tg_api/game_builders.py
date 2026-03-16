import random

from app.backend.store.bot.callbacks import (
    StartGameCallback,
    JoinGameCallback,
    EndGameCallback,
    ContinueGameCallback,
)

from app.backend.store.tg_api.game_constraints import (
    CompanySharesModelNames,
    CompanySharesModelBasePrices,
    EventList
)

# ── Статичные клавиатуры (reply-keyboard) ────────────────────────────────────

MAIN_MENU_TEXT = "🏠 Главное меню"

MAIN_MENU_BUTTONS = [
    ["Начать игру", "Покинуть игру"],
    ["Показать статистику", "Правила игры"],
]

GAME_MENU_BUTTONS = [
    ["⏭ Завершить Ход", "🏁 Завершить игру"],
    ["Купить Акции", "Продать Акции"],
    ["Просмотреть портфель"],
]

RULES_TEXT = (
    "📖 *Правила игры «Биржа»*\n\n"
    "1. Каждый игрок начинает с одинаковым капиталом.\n"
    "2. В каждом раунде цены на акции меняются.\n"
    "3. Покупайте дёшево — продавайте дорого.\n"
    "4. Когда все игроки завершат ход, начинается следующий раунд.\n"
    "5. Победитель — игрок с максимальным капиталом на конец игры.\n"
)


# ── События ─────────────────────────────────────────────────────────────────────

def get_random_events(companies: list[dict]) -> list[dict[str, int]]:
    """
    Для каждой компании генерирует случайное событие.
    Возвращает: [{"name": str, "old_price": float, "new_price": float, "direction": str, "percent": int}]
    """
    events = []
    for company in companies:
        percent = random.choices(EventList.values, EventList.chances)[0]
        direction = random.choice(EventList.directions)

        old_price = company["price"]
        if direction == "up":
            new_price = round(old_price * (1 + percent / 100), 2)
        else:
            new_price = round(max(1.0, old_price * (1 - percent / 100)), 2)

        # TODO изменение цен компаний можно записывать в БД (мб потом переделать, добавив новую таблицу + связи к ней)
        events.append({
            "name": company["name"],
            "old_price": old_price,
            "new_price": new_price,
            "direction": direction,
            "percent": percent,
        })

    return events

# ── Лобби ────────────────────────────────────────────────────────────────────

def build_lobby_message(user_names: list[str], game_id: int) -> tuple[str, list]:
    """Возвращает (текст, inline-клавиатура) для сообщения лобби."""
    players_text = "\n".join(f"  • {n}" for n in user_names) if user_names else "  — пока никого"
    text = (
        f"🎮 *Лобби игры #{game_id}*\n\n"
        f"Игроки ({len(user_names)}):\n{players_text}\n\n"
        "Нажмите кнопку, чтобы присоединиться или начать игру."
    )
    keyboard = [[
        {"text": "✅ Начать игру",        "callback_data": StartGameCallback.build(game_id=game_id)},
        {"text": "🚪 Присоединиться",     "callback_data": JoinGameCallback.build(game_id=game_id)},
    ]]
    return text, keyboard


def build_lobby_entrance_message(user, game_id: int) -> str:
    name = user.name if user else "Игрок"
    return f"👋 {name} присоединился к лобби #{game_id}!"


def build_lobby_exit_message(user, game_id: int) -> str:
    name = user.name if user else "Игрок"
    return f"🚶 {name} покинул лобби #{game_id}."


# ── Начало игры ───────────────────────────────────────────────────────────────

def build_game_start_text(user_names: list[str], game_id: int) -> str:
    players_text = "\n".join(f"  • {n}" for n in user_names)
    return (
        f"🚀 *Игра #{game_id} началась!*\n\n"
        f"Участники:\n{players_text}\n\n"
        "Используйте кнопки ниже для управления.\n"
    )

# ── Начало раунда ─────────────────────────────────────────────────────────────
 
def build_round_start_message(
    round_num: int,
    players_balances: list[dict],
    events: list[dict],
) -> str:
    """
    players_balances — [{"name": str, "balance": float}]
    events           — результат get_random_events()
    """
    # Рейтинг игроков
    balances_sorted = sorted(players_balances, key=lambda x: x["balance"], reverse=True)
    balances_lines = "\n".join(
        f"  {i + 1}. *{p['name']}* — {p['balance']:.2f} ₽"
        for i, p in enumerate(balances_sorted)
    )

    # Изменения цен акций
    price_lines = []
    for e in events:
        if e["direction"] == "none":
            price_lines.append(f"  ➡️ *{e['name']}*: {e['new_price']:.2f} ₽")
        else:
            arrow = "📈" if e["direction"] == "up" else "📉"
            sign  = "+" if e["direction"] == "up" else "-"
            diff  = abs(e["new_price"] - e["old_price"])
            price_lines.append(
                f"  {arrow} *{e['name']}*: "
                f"{e['old_price']:.2f} ₽ → {e['new_price']:.2f} ₽  "
                f"({sign}{e['percent']}%, {sign}{diff:.2f} ₽)"
            )
    prices_text = "\n".join(price_lines)

    return (
        f"⏳ *Раунд {round_num} начался!*\n\n"
        f"💰 *Рейтинг игроков:*\n{balances_lines}\n\n"
        f"📊 *Изменения цен акций:*\n{prices_text}"
    )
    
# ── Подтверждение завершения игры ─────────────────────────────────────────────
 
def build_end_game_confirm_keyboard(game_id: int) -> list:
    return [[
        {"text": "✅ Да, завершить",   "callback_data": EndGameCallback.build(game_id=game_id)},
        {"text": "❌ Нет, продолжить", "callback_data": ContinueGameCallback.build(game_id=game_id)},
    ]]

# ── Компании ─────────────────────────────────────────────────────────────────────

def get_initial_companies() -> list[dict]:
    """Возвращает список компаний с базовыми ценами для создания при старте игры."""
    return [
        {"name": CompanySharesModelNames.tg_shares,       "price": CompanySharesModelBasePrices.tg_shares},
        {"name": CompanySharesModelNames.vk_shares,       "price": CompanySharesModelBasePrices.vk_shares},
        {"name": CompanySharesModelNames.hamster_shares,  "price": CompanySharesModelBasePrices.hamster_shares},
        {"name": CompanySharesModelNames.big_data_shares, "price": CompanySharesModelBasePrices.big_data_shares},
    ]

# ── Акции: покупка ────────────────────────────────────────────────────────────
 
def build_buy_companies_message(companies: list, balance: float) -> str:
    """
    Показывает список акций с ценами и готовой командой покупки 1 акции.
    companies — [{"name": str, "price": float}]
    """
    if not companies:
        return "📈 Акций для покупки нет."
 
    lines = [
        f"  • *{c['name']}* — {c['price']:.2f} ₽\n"
        f"    👉 `/buy {c['name']} 1`"
        for c in companies
    ]
 
    return (
        f"📈 *Доступные акции*\n\n"
        + "\n\n".join(lines) +
        f"\n\n💰 Ваш баланс: *{balance:.2f} ₽*\n\n"
        f"Команда: `/buy НАЗВАНИЕ КОЛИЧЕСТВО`\n"
        f"Например: `/buy TELEGRAM 5`"
    )
 
# ── Акции: продажа ────────────────────────────────────────────────────────────
 
def build_sell_portfolio_message(portfolio: list, balance: float) -> str:
    """
    Показывает портфель игрока с командой продажи 1 акции каждой позиции.
    portfolio — [{"name": str, "quantity": int, "price": float}]
    """
    if not portfolio:
        return (
            f"💼 *Ваш портфель пуст* — нечего продавать.\n\n"
            f"💰 Баланс: *{balance:.2f} ₽*"
        )
 
    lines = []
    total_shares_value = 0.0
    for p in portfolio:
        position_value = p["quantity"] * p["price"]
        total_shares_value += position_value
        lines.append(
            f"  • *{p['name']}*: {p['quantity']} шт. × {p['price']:.2f} ₽ = {position_value:.2f} ₽\n"
            f"    👉 `/sell {p['name']} 1`"
        )
 
    return (
        f"💼 *Ваш портфель*\n\n"
        + "\n\n".join(lines) +
        f"\n\n💵 Стоимость акций: *{total_shares_value:.2f} ₽*\n"
        f"💰 Свободный баланс: *{balance:.2f} ₽*\n\n"
        f"Команда: `/sell НАЗВАНИЕ КОЛИЧЕСТВО`\n"
        f"Например: `/sell TELEGRAM 3`"
    )

# ── Просмотр портфеля ─────────────────────────────────────────────────────────
 
def build_portfolio_message(user, portfolio: list, balance: float) -> str:
    if not portfolio:
        lines_text = "  — портфель пуст"
        total_shares_value = 0.0
    else:
        total_shares_value = sum(p["quantity"] * p["price"] for p in portfolio)
        lines = [
            f"  • *{p['name']}*: {p['quantity']} шт. × {p['price']:.2f} ₽ = {p['quantity'] * p['price']:.2f} ₽"
            for p in portfolio
        ]
        lines_text = "\n".join(lines)
 
    return (
        f"💼 *Портфель {user.name}*\n\n"
        f"{lines_text}\n\n"
        f"💵 Стоимость акций: *{total_shares_value:.2f} ₽*\n"
        f"💰 Свободный баланс: *{balance:.2f} ₽*\n"
        f"📊 Итого: *{balance + total_shares_value:.2f} ₽*"
    )

# ── Завершение игры ─────────────────────────────────────────────────────────

def build_game_over_message(
    round_num: int,
    players_balances: list[dict],
) -> str:
    """
    round_num        — количество сыгранных раундов.
    players_balances — [{"name": str, "balance": float}]
    """
    sorted_players = sorted(players_balances, key=lambda x: x["balance"], reverse=True)

    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for i, p in enumerate(sorted_players):
        medal = medals[i] if i < len(medals) else f"  {i + 1}."
        lines.append(f"{medal} *{p['name']}* — {p['balance']:.2f} ₽")

    players_text = "\n".join(lines)
    winner = sorted_players[0]["name"] if sorted_players else "—"

    return (
        f"🏁 *Игра завершена!*\n\n"
        f"Сыграно раундов: *{round_num}*\n\n"
        f"🏆 *Итоговый рейтинг:*\n{players_text}\n\n"
        f"👑 Победитель: *{winner}*"
    )

# ── Статистика ────────────────────────────────────────────────────────────────

def build_stats_message(user) -> str:
    games_played = getattr(user, 'games_played', 0)
    games_won = getattr(user, 'games_won', 0)  # ← было user.wins
    win_rate = (games_won / games_played * 100) if games_played > 0 else 0

    return (
        f"📊 *Статистика игрока {user.name}*\n\n"
        f"Игр сыграно: {games_played}\n"
        f"Побед: {games_won}\n"
        f"Процент побед: {win_rate:.1f}%\n"
        f"Максимальный баланс: {float(user.max_balance):.2f} ₽\n"
    )