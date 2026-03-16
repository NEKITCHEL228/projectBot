class MainMenuButtons:
    start_game = "Начать игру"
    leave_game = "Покинуть игру"
    show_stats = "Показать статистику"
    show_rules = "Правила игры"


class BotCommands:
    start_game = "/start_game"
    show_stats = "/stats"
    show_rules = "/rules"
    leave_game = "/leave"
    buy_shares = "/buy_shares"
    sell_shares = "/sell_shares"
    show_portfolio = "/show_portfolio"


class GameButtons:
    buy_shares    = "Купить Акции"
    sell_shares   = "Продать Акции"
    show_portfolio = "Просмотреть портфель"
    end_turn      = "⏭ Завершить Ход"
    end_game      = "🏁 Завершить игру"

class GameCommands:
    buy_shares    = "/buy_shares"
    sell_shares   = "/sell_shares"
    show_portfolio = "/show_portfolio"
    end_turn      = "/end_turn"
    end_game      = "/end_game"
    buy            = "/buy"
    sell           = "/sell"


class CompanySharesModelNames:
    tg_shares = "TELEGRAM"
    vk_shares = "VK"
    hamster_shares = "HAMSTERCOMBAT"
    big_data_shares = "BIGDATA"
    
class CompanySharesModelBasePrices:
    tg_shares = 50
    vk_shares = 30
    hamster_shares = 15
    big_data_shares = 80
    
class EventList:
    values = [3, 8, 15, 20, 30, 50, 99, 228, 777, 1000]

    chances = [
        0.25,
        0.20,
        0.15,
        0.12,
        0.10,
        0.07,
        0.05,
        0.03,
        0.02,
        0.01,
    ]
    
    directions = ["up", "down"]