from typing import TYPE_CHECKING

from app.backend.store.database.database import Database

if TYPE_CHECKING:
    from app.backend.web.app import Application

class Store:
    def __init__(self, app: "Application"):
        from app.backend.store.admin.accessor import AdminAccessor
        from app.backend.store.bot.manager import BotManager
        from app.backend.store.game.accessor import GameAccessor
        from app.backend.store.user.accessor import UserAccessor
        from app.backend.store.tg_api.accessor import TgApiAccessor

        self.admins = AdminAccessor(app)
        self.bots_manager = BotManager(app)
        self.games = GameAccessor(app)
        self.users = UserAccessor(app)
        self.tg_api = TgApiAccessor()


def setup_store(app: "Application"):
    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_cleanup.append(app.database.disconnect)
    app.store = Store(app)
        