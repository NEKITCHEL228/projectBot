from typing import TYPE_CHECKING

from app.backend.store.bot.commands import setup_commands
from app.backend.base.base_accessor import BaseAccessor

import aiohttp

from app.backend.store.tg_api.poller import Poller

if TYPE_CHECKING:
    from app.backend.web.app import Application
    
class TgApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)

        self.session: aiohttp.ClientSession | None = None
        self.token: str | None = None
        self.server: str | None = None
        self.poller: Poller | None = None
        self.ts: int | None = None

    async def connect(self, app: "Application"):
        self.token = app.config.bot.token
        self.server = f"https://api.telegram.org/bot{self.token}"
        self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False))
        await setup_commands(self.session, self.server)
        self.poller = Poller(app.store)
        self.poller.start()

    async def disconnect(self, app: "Application"):
        self.poller.is_running = False
        if self.session:
            await self.session.close()
    
    async def poll(self) -> None:
        params: dict = {"timeout": 25}
        if self.ts is not None:
            params["offset"] = self.ts

        try:
            async with self.session.get(
                f"{self.server}/getUpdates",
                params=params,
            ) as response:
                data = await response.json()
        except Exception as e:
            self.logger.error(f"Failed to poll Telegram API: {e}")
            return

        if not data.get("ok", False):
            self.logger.error(f"Telegram API error: {data.get('description', 'Unknown error')}")
            return

        updates = data.get("result", [])
        if updates:
            self.ts = updates[-1]["update_id"] + 1
            await self.app.store.bots_manager.handle_updates(updates)