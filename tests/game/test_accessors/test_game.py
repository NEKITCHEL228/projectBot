import pytest

from app.backend.game.models import GameStatusEnum

class TestGameActiveGame:
    async def test_waiting_game(self, game_accessor, game):
        result = await game_accessor.get_active_game(game.chat_id)
        assert result is not None
        assert result.game_id == game.game_id
        assert result.game_status == GameStatusEnum.WAITING_FOR_PLAYERS