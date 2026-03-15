from typing import TYPE_CHECKING

from app.backend.store.bot.commands import setup_commands, setup_buttons
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
        await setup_commands(self.session, self.server, app)
        await setup_buttons(self.session, self.server, app)
        self.poller = Poller(app.store)
        self.poller.start()

    async def disconnect(self, app: "Application"):
        self.poller.is_running = False
        if self.session:
            await self.session.close()
    
    async def poll(self) -> None:
        url = f"{self.server}/getUpdates"
        params: dict = {"timeout": 25}
        if self.ts is not None:
            params["offset"] = self.ts

        try:
            async with self.session.get(url,params=params) as response:
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
            
    async def send_message(self, chat_id: int, text: str) -> None:
        url = f"{self.server}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
        }
        await self.session.post(url, json=payload)
        
    async def send_keyboard(self, chat_id: int, text: str, keyboard: list[list[dict[str, str]]]) -> None:
        url = f"{self.server}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "reply_markup": {
                "keyboard": keyboard,
                "resize_keyboard": True
            }
        }
        await self.session.post(url, json=payload)
        
    async def edit_message(self, chat_id: int, message_id: int, text: str) -> None:
        url = f"{self.server}/editMessageText"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
        }
        await self.session.post(url, json=payload)
        
    async def delete_message(self, chat_id: int, message_id: int) -> None:
        url = f"{self.server}/deleteMessage"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
        }
        await self.session.post(url, json=payload)

    async def send_inline_keyboard(self, chat_id: int, text: str, keyboard: list[list[dict]]) -> None:
        url = f"{self.server}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "reply_markup": {"inline_keyboard": keyboard},
        }
        await self.session.post(url, json=payload)

    async def answer_callback_query(self, callback_query_id: str) -> None:
        url = f"{self.server}/answerCallbackQuery"
        await self.session.post(url, json={"callback_query_id": callback_query_id})