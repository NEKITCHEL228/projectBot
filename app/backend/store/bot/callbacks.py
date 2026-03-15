class CallbackBase:
    prefix: str

    def __init__(self, **data):
        for key, value in data.items():
            setattr(self, key, value)

    @classmethod
    def from_data(cls, data: str):
        parts = data.split(":")
        kwargs = {}

        fields = cls.__annotations__.keys()

        for field, value in zip(fields, parts[1:]):
            field_type = cls.__annotations__[field]
            kwargs[field] = field_type(value)

        return cls(**kwargs)

    @classmethod
    def build(cls, **kwargs):
        values = ":".join(str(v) for v in kwargs.values())
        return f"{cls.prefix}:{values}"


class StartGameCallback(CallbackBase):
    prefix = "start_game"
    game_id: int


class JoinGameCallback(CallbackBase):
    prefix = "join_game"
    game_id: int


class ContinueGameCallback(CallbackBase):
    prefix = "continue_game"
    game_id: int


class RequestEndGameCallback(CallbackBase):
    prefix = "request_end_game"
    game_id: int


class EndGameCallback(CallbackBase):
    prefix = "end_game"
    game_id: int


class SwapGameRoundCallback(CallbackBase):
    prefix = "swap_game_round"
    game_id: int


class EndTurnVoteCallback(CallbackBase):
    prefix = "end_turn_vote"
    game_id: int
