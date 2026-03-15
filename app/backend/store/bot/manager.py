from typing import TYPE_CHECKING
from logging import getLogger

from app.backend.store.tg_api.schemes import Update, User, Chat, Message, CallbackQuery

if TYPE_CHECKING:
    from app.backend.web.app import Application
    from app.backend.store.bot.router import BotRouter
    

class BotManager:
    def __init__(self, app: "Application", router: "BotRouter"):
        self.app = app
        self.router = router
        self.logger = getLogger("BotManager")

    async def handle_updates(self, updates):
        for update in updates:
            validate_update = Update.model_validate(update)
            self.logger.info(f"Received update: {validate_update}")
            
            if validate_update.message:
                message = validate_update.message
                chat_id = message.chat.id
                text = message.text or ""
                user_id = message.from_user.id if message.from_user else None

                if user_id:
                    user = await self.app.store.users.get_by_tg_id(user_id)
                    if not user:
                        await self.app.store.users.create_user(user_id)

                await self.router.route_message(self, chat_id, user_id, text)

            elif validate_update.callback_query:
                cb = validate_update.callback_query
                user_id = cb.from_user.id
                chat_id = cb.message.chat.id if cb.message else None
                data = cb.data or ""

                if chat_id and data:
                    await self.router.route_callback(self, chat_id, user_id, data)

                await self.app.store.tg_api.answer_callback_query(cb.id)
                        
                    
        
        

    