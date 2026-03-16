from typing import TYPE_CHECKING, Callable, Awaitable

if TYPE_CHECKING:
    from app.backend.store.bot.manager import BotManager


class BotRouter:
    def __init__(self):
        # text/command -> handler
        self._message_handlers: dict[str, Callable] = {}
        # prefix команды (/buy, /sell) -> handler
        self._command_handlers: dict[str, Callable] = {}
        # callback prefix -> handler
        self._callback_handlers: dict[str, Callable] = {}
        # pending action key -> handler  ("buy" | "sell" | ...)
        self._pending_handlers: dict[str, Callable] = {}

    # ── Декораторы ────────────────────────────────────────────────────────────

    def message(self, *triggers: str):
        """Регистрирует обработчик сообщений/команд по одному или нескольким триггерам."""
        def decorator(func: Callable):
            for trigger in triggers:
                self._message_handlers[trigger] = func
            return func
        return decorator
    
    def command(self, *prefixes: str):
        """
        Команды с аргументами: /buy TELEGRAM 5, /sell VK 3.
        Совпадение по первому слову сообщения.
        """
        def decorator(func: Callable):
            for prefix in prefixes:
                self._command_handlers[prefix] = func
            return func
        return decorator

    def callback(self, callback_cls):
        """Регистрирует обработчик callback_query по префиксу класса."""
        def decorator(func: Callable):
            self._callback_handlers[callback_cls.prefix] = (callback_cls, func)
            return func
        return decorator

    def pending(self, action: str):
        """Регистрирует обработчик ожидающего ввода (pending action)."""
        def decorator(func: Callable):
            self._pending_handlers[action] = func
            return func
        return decorator

    # ── Роутинг ───────────────────────────────────────────────────────────────

    async def route_message(
        self,
        manager: "BotManager",
        chat_id: int,
        user_id: int,
        text: str,
    ) -> None:
        # 1. Проверяем pending-действие для пользователя
        pending_action = manager.get_pending_action(chat_id, user_id)
        if pending_action and not text.startswith("/"):
            handler = self._pending_handlers.get(pending_action)
            if handler:
                await handler(manager, chat_id, user_id, text)
                return

        # 2. Команды с аргументами (/buy TELEGRAM 5, /sell VK 3)
        first_word = text.split()[0] if text.split() else ""
        cmd_handler = self._command_handlers.get(first_word)
        if cmd_handler:
            await cmd_handler(manager, chat_id, user_id, text)
            return
 
        # 3. Точное совпадение (reply-кнопки и простые команды без аргументов)
        handler = self._message_handlers.get(text)
        if handler:
            await handler(manager, chat_id, user_id)

    async def route_callback(
        self,
        manager: "BotManager",
        chat_id: int,
        user_id: int,
        data: str,
    ) -> None:
        prefix = data.split(":")[0]
        entry = self._callback_handlers.get(prefix)
        if entry:
            callback_cls, handler = entry
            callback_obj = callback_cls.from_data(data)
            await handler(manager, chat_id, user_id, callback_obj)