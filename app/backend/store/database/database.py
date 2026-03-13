from typing import TYPE_CHECKING

from sqlalchemy import select, URL
from sqlalchemy.ext.asyncio import (
    AsyncSession, 
    AsyncEngine, 
    async_sessionmaker
)
from sqlalchemy import create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.backend.store.database.sqlalchemy_base import BaseModel

if TYPE_CHECKING:
    from app.backend.web.app import Application

class Database:
    def __init__(self, app: "Application"):
        self.app = app

        self.engine: AsyncEngine | None = None
        self._database: type[DeclarativeBase] = BaseModel
        self.session: async_sessionmaker[AsyncSession] | None = None

    async def connect(self, app: "Application"):
        self.engine = create_async_engine(
            URL.create(drivername="postgresql+asyncpg", 
                       username=self.app.config.db_user, 
                       password=self.app.config.db_password, 
                       host=self.app.config.db_host, 
                       port=self.app.config.db_port, 
                       database=self.app.config.db_name),
        )

        self.session = async_sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False)

        async with self.engine.begin() as conn:
            await conn.run_sync(self._database.metadata.create_all)

    async def disconnect(self):
        if self.engine:
            await self.engine.dispose()
