import aiohttp


async def setup_commands(session: aiohttp.ClientSession, server: str) -> None:
    await session.post(
        f"{server}/setMyCommands",
        json={"commands": get_bot_main_menu_commands()},
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
