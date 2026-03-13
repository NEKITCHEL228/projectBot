from typing import TYPE_CHECKING
from logging import getLogger


if TYPE_CHECKING:
    from app.backend.web.app import Application

class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("BotManager")

    async def handle_updates(self, updates):
        self.logger.info(f"Received updates: {updates}")

    