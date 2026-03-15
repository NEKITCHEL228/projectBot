from app.backend.store.tg_api.game_constraints import MainMenuButtons, GameButtons, BotCommands, LobbyButtons

MAIN_MENU_TEXT = f"Главное меню:\n" \
            f"1. {MainMenuButtons.start_game} - {BotCommands.start_game}\n" \
            f"2. {MainMenuButtons.join_game} - {BotCommands.join_game}\n" \
            f"3. {MainMenuButtons.show_stats} - {BotCommands.show_stats}\n" \
            f"4. {MainMenuButtons.show_rules} - {BotCommands.show_rules}\n"

STATS_TEXT = "Статистика игрока:\n" \

GAME_MENU_TEXT = f"Меню игры:\n" \
            f"1. {GameButtons.hamster_shares} - Купить/Продать акции Hamster Combat\n" \
            f"2. {GameButtons.durev_shares} - Купить/Продать акции Durev\n" \
            f"3. {GameButtons.vk_shares} - Купить/Продать акции VK\n" \
            f"4. {GameButtons.show_portfolio} - Показать портфель\n" \
            f"5. {GameButtons.end_turn} - Завершить ход\n" \
            f"6. {GameButtons.end_game} - Завершить игру\n"
            
RULES_TEXT = "Правила игры:\n" \
             "1. Цель игры - заработать больше всего денег, покупая и продавая акции компаний.\n" \
             "2. В начале игры каждому игроку выдается 1000 ₽.\n" \
             "3. Игроки могут покупать или продавать акции компаний по текущей цене.\n" \
             "4. Цена акций может изменяться в зависимости от действий игроков и случайных событий.\n" \
             "5. Игра заканчивается, когда один из игроков достигает определенной суммы денег или по истечении определенного количества ходов.\n" \
             "6. Побеждает игрок с наибольшим количеством денег в конце игры."
             
MAIN_MENU_BUTTONS = [
        [{"text": MainMenuButtons.start_game}, {"text": MainMenuButtons.join_game}],
        [{"text": MainMenuButtons.show_stats}, {"text": MainMenuButtons.show_rules}]
    ]

GAME_MENU_BUTTONS = [
        [{"text": GameButtons.hamster_shares}, {"text": GameButtons.durev_shares}, {"text": GameButtons.vk_shares}],
        [{"text": GameButtons.show_portfolio}], 
        [{"text": GameButtons.end_turn}, {"text": GameButtons.end_game}]
    ]

LOBBY_BUTTONS = [
    [{"text": LobbyButtons.leave_game}],
    [{"text": LobbyButtons.show_stats}, {"text": LobbyButtons.show_rules}]
]

UNCORRECT_MESSAGE = f"Неккоректное сообщение! Попробуйте снова."


def build_lobby_entarance_message(user, game_id: int) -> str:
    return f"{user.name} присоединятеся к лобби {game_id}"

def build_lobby_exit_message(user, game_id: int) -> str:
    return f"{user.name} выходит из лобби {game_id}"

def build_lobby_message(user_names: list[str], game_id: int) -> tuple[str, list]:
    if user_names:
        user_text = "\n".join(f"• {name}" for name in user_names)
    else:
        user_text = "  пока никого нет"
    text = (
        f"🎮 Лобби игры (id: {game_id})\n"
        f"Игроки ({len(user_names)}):\n"
        f"{user_text}\n\n"
        f"Нажмите кнопку ниже, чтобы начать игру."
    )
    keyboard = [[{"text": "🚀 Начать игру", "callback_data": f"start_game:{game_id}"}]]
    return text, keyboard

def build_stats_message(user) -> str:
    winrate = (
        round(user.games_won / user.games_played * 100)
        if user.games_played > 0
        else 0
    )
    return (
        f"📊 Статистика игрока {user.name}:\n\n"
        f"🏆 Побед: {user.games_won}\n"
        f"🎮 Игр сыграно: {user.games_played}\n"
        f"📈 Процент побед: {winrate}%\n"
        f"💰 Рекордный баланс: {user.max_balance:.2f}₽"
    )

def build_company_shares_prices_text(companies: list) -> str:
    if not companies:
        return "📉 Нет доступных акций."
    lines = "\n".join(
        f"• {company.name}: {company.price:.2f} ₽/акция"
        for company in companies
    )
    return f"📊 Текущие цены акций:\n\n{lines}"


def build_game_start_text(user_names: list[str], game_id: int, round_num: int = 1) -> str:
    players_lines = "\n".join(
        f"• {name} — 💰 1000.00 ₽ | 📦 0 акций"
        for name in user_names
    )
    return (
        f"🎮 Игра (id: {game_id}) началась! Удачи всем участникам!\n\n"
        f"👥 Игроки ({len(user_names)}):\n{players_lines}\n\n"
        f"🔄 Раунд {round_num}"
    )