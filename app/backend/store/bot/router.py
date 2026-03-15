from typing import TYPE_CHECKING, Any

from app.backend.store.bot.callbacks import CallbackBase
from app.backend.store.tg_api.game_builders import UNCORRECT_MESSAGE

if TYPE_CHECKING:
    from app.backend.store.bot.manager import BotManager

class BotRouter:
    def __init__(self):
        self.message_handlers = {}
        self.callback_handlers = {}
        
    def message(self, *commands: str):
        def decorator(func):
            for command in commands:
                self.message_handlers[command] = func
            return func
        return decorator
    
    def callback(self, trigger: Any):
        def decorator(func):
            if isinstance(trigger, type) and issubclass(trigger, CallbackBase):
                self.callback_handlers[trigger.prefix] = (func, trigger)
            else:
                self.callback_handlers[trigger] = (func, None)
            return func
        return decorator
    
    async def route_message(self, manager: "BotManager", chat_id: int, user_id: int, text: str):
        handler = self.message_handlers.get(text)
        if handler:
            await handler(manager, chat_id, user_id)
        else:
            await manager.app.store.tg_api.send_message(chat_id, UNCORRECT_MESSAGE)

    async def route_callback(self, manager: "BotManager", chat_id: int, user_id: int, data: str):
        prefix = data.split(":")[0]
        handler_info = self.callback_handlers.get(prefix)
        if handler_info:
            func, callback_cls = handler_info
            callback = callback_cls.from_data(data) if callback_cls else None
            await func(manager, chat_id, user_id, callback)