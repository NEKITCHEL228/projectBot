class CallbackBase:
    prefix: str

    def __init__(self, **data):
        for key, value in data.items():
            setattr(self, key, value)

    @classmethod
    def from_data(cls, data: str):
        parts = data.split(":")
        kwargs = {}
        fields = list(cls.__annotations__.keys())
        for field, value in zip(fields, parts[1:]):
            field_type = cls.__annotations__[field]
            kwargs[field] = field_type(value)
        return cls(**kwargs)

    @classmethod
    def build(cls, **kwargs):
        values = ":".join(str(v) for v in kwargs.values())
        return f"{cls.prefix}:{values}"


# ── Лобби ────────────────────────────────────────────────────────────────────

class StartGameCallback(CallbackBase):
    """Создатель лобби нажал «Начать игру» в inline-сообщении лобби."""
    prefix = "start_game"
    game_id: int


class JoinGameCallback(CallbackBase):
    """Игрок нажал «Присоединиться к игре» в inline-сообщении лобби."""
    prefix = "join_game"
    game_id: int


# ── Управление игрой ─────────────────────────────────────────────────────────

class EndGameCallback(CallbackBase):
    """Подтверждение завершения игры (кнопка «Да»)."""
    prefix = "end_game"
    game_id: int


class ContinueGameCallback(CallbackBase):
    """Отмена — продолжить игру (кнопка «Нет» / «Отмена»)."""
    prefix = "continue_game"
    game_id: int

class NextTurnCallback(CallbackBase):
    prefix = "next_turn"
    game_id: int
