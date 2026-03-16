import pytest
import pytest_asyncio
import os
from aiohttp.test_utils import loop_context
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.backend.game.models import GameModel, GameStatusEnum
from app.backend.web.app import setup_app, Application
from app.backend.store.database.database import Database


@pytest.fixture(scope="session")
def event_loop():
    with loop_context() as loop:
        yield loop


@pytest.fixture(scope="session")
def application() -> Application:
    app = setup_app(
        config_path=os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "config.yml"
        )
    )
    app.on_startup.clear()
    app.on_shutdown.clear()
    app.on_cleanup.clear()
    app.database = Database(app)
    return app


@pytest_asyncio.fixture(scope="session")
async def connect_db(application: Application):
    await application.database.connect(application)
    yield application
    await application.database.disconnect(application)


@pytest_asyncio.fixture(autouse=True)  # запускается для каждого теста
async def clean_tables(connect_db: Application):
    yield
    # очистка ПОСЛЕ теста
    async with connect_db.database.session() as session:
        async with session.begin():
            for table in reversed(
                connect_db.database._database.metadata.sorted_tables
            ):
                await session.execute(text(f"TRUNCATE {table.name} CASCADE"))


@pytest.fixture
def store(connect_db: Application):
    return connect_db.store


@pytest.fixture
def game_accessor(connect_db: Application):
    return connect_db.store.games


@pytest_asyncio.fixture
async def game(connect_db: Application):
    async with connect_db.database.session() as session:
        g = GameModel(
            chat_id=200002,
            game_status=GameStatusEnum.WAITING_FOR_PLAYERS,
            max_rounds=10,
            game_trading_session_round=1,
        )
        session.add(g)
        await session.commit()
        await session.refresh(g)
    return g