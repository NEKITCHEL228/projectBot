class CallbackBase:
    prefix: str

    @classmethod
    def from_data(cls, data: str) -> "CallbackBase":
        raise NotImplementedError


class StartGameCallback(CallbackBase):
    prefix = "start_game"

    def __init__(self, game_id: int):
        self.game_id = game_id

    @classmethod
    def from_data(cls, data: str) -> "StartGameCallback":
        game_id = int(data.split(":")[1])
        return cls(game_id)

    @staticmethod
    def build(game_id: int) -> str:
        return f"start_game:{game_id}"
