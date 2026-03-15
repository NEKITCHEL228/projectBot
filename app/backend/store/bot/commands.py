from typing import TYPE_CHECKING
import aiohttp

if TYPE_CHECKING:
    from app.backend.web.app import Application


async def setup_commands(session: aiohttp.ClientSession, server: str, app: "Application") -> None:
    #команды для всех пользователей
    await session.post(
        f"{server}/setMyCommands",
        json={
            "commands": get_bot_main_menu_commands(),
              "scope": {"type": "default"},
              },
    )
    #команды для админов
    for admin in await app.store.admins.get_list_admins():
        await session.post(
            f"{server}/setMyCommands",
            json={
                "commands": get_bot_admin_menu_commands(),
                "scope": {"type": "chat", "chat_id": admin.tg_id},
            },
        )
async def setup_buttons(session: aiohttp.ClientSession, server: str, app: "Application") -> None:
    #кнопки для всех пользователей
    await session.post(
        f"{server}/sendMessage",
        json={
            "text": "Главное меню:",
            "reply_markup": {
                "keyboard": [
                    [{"text": "Начать игру", "callback_data": "play"}],
                    [{"text": "Присоединиться к игре", "callback_data": "help"}],
                    [{"text": "Показать статистику", "callback_data": "stats"}],
                    [{"text": "Правила игры", "callback_data": "rules"}],
                ],
                "resize_keyboard": True
            }
        },
    )


def get_bot_main_menu_commands() -> list[dict[str, str]]:
    return [
        {"command": "start", "description": "Start the bot"},
        {"command": "help", "description": "Show help message"},
        {"command": "play", "description": "Play the game"},
        {"command": "stop", "description": "Stop the game"},
    ]

def get_bot_admin_menu_commands() -> list[dict[str, str]]:
    return [
        {"command": "admin", "description": "Admin commands"},
        {"command": "stats", "description": "Show game statistics"},
        {"command": "broadcast", "description": "Broadcast a message to all users"},
    ]

def get_bot_game_commands() -> list[dict[str, str]]:
    return [
        {"command": "move", "description": "Make a move in the game"},
        {"command": "status", "description": "Show current game status"},
        {"command": "quit", "description": "Quit the current game"},
    ]
