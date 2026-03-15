from app.backend.store.tg_api.game_constraints import MainMenuButtons, GameButtons, BotCommands

MAIN_MENU_TEXT = f"Главное меню:\n" \
            f"1. {MainMenuButtons.start_game} - {BotCommands.start_game}\n" \
            f"2. {MainMenuButtons.join_game} - {BotCommands.join_game}\n" \
            f"3. {MainMenuButtons.show_stats} - {BotCommands.show_stats}\n" \
            f"4. {MainMenuButtons.show_rules} - {BotCommands.show_rules}\n"
            
GAME_LOBBY_TEXT = "Вы находитесь в лобби игры. Ожидайте начала игры или присоединяйтесь к другой игре.\n" \
                    "Игроки в лобби:\n" \

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
             "2. В начале игры каждому игроку выдается определенная сумма денег.\n" \
             "3. Игроки по очереди могут покупать или продавать акции компаний по текущей цене.\n" \
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

UNCORRECT_MESSAGE = f"Неккоректное сообщение! Попробуйте снова."


def build_lobby_message(players_tg_ids: list[int], game_id: int) -> tuple[str, list]:
    if players_tg_ids:
        players_text = "\n".join(f"• {tg_id}" for tg_id in players_tg_ids)
    else:
        players_text = "  пока никого нет"
    text = (
        f"🎮 Лобби игры (id: {game_id})\n"
        f"Игроки ({len(players_tg_ids)}):\n"
        f"{players_text}\n\n"
        f"Нажмите кнопку ниже, чтобы начать игру."
    )
    keyboard = [[{"text": "🚀 Начать игру", "callback_data": f"start_game:{game_id}"}]]
    return text, keyboard