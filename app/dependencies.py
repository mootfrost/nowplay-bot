from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession
from app.db import async_session


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


@asynccontextmanager
async def get_session_context() -> AsyncSession:
    async with async_session() as session:
        yield session
