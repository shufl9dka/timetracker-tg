from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from models.base import Base

from conf.app import Config


engine: AsyncEngine = create_async_engine(Config.SQL_ENGINE_URI)
async_session = async_sessionmaker(engine)


async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
