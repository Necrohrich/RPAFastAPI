#app/infrastructure/db/database.py
from contextlib import asynccontextmanager

from app.infrastructure.models.base_model import BaseModel
from app.utils.files import load_json
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

config = load_json("secrets.json")
DATABASE_URL = config["DATABASE_URL"]
#Создает асинхронный engine — пул соединений с БД.
engine = create_async_engine(DATABASE_URL, echo=True, pool_pre_ping=True)
#Фабрика асинхронных сессий для работы с БД.
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession)

async def init_db():
    """Определяет действия с таблицей при инициализации сервера"""
    async with engine.begin() as conn:
        # удаление всех таблиц
        #await conn.run_sync(BaseModel.metadata.drop_all)
        # создание всех таблиц
        await conn.run_sync(BaseModel.metadata.create_all)
        print(BaseModel.metadata.tables.keys())

@asynccontextmanager
async def get_session():
    """Создает сессии для работы с БД"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise Exception(f"Ошибка: {e}")

async def close_engine():
    await engine.dispose()