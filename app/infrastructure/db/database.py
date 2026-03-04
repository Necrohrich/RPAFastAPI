#app/infrastructure/db/database.py
from app.core.config import settings
from app.infrastructure.models.base_model import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

#Создает асинхронный engine — пул соединений с БД.
engine = create_async_engine(settings.DATABASE_URL, echo=True, pool_pre_ping=True)
#Фабрика асинхронных сессий для работы с БД.
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession,expire_on_commit=False)

async def init_db():
    """Определяет действия с таблицей при инициализации сервера"""
    async with engine.begin() as conn:
        # удаление всех таблиц
        # await conn.run_sync(BaseModel.metadata.drop_all)
        # создание всех таблиц
        # await conn.run_sync(BaseModel.metadata.create_all)
        print(BaseModel.metadata.tables.keys())

class UnitOfWork:
    def __init__(self):
        self.session = None

    async def __aenter__(self):
        self.session = AsyncSessionLocal()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            if exc:
                await self.session.rollback()
            else:
                await self.session.commit()
        finally:
            await self.session.close()

async def get_uow():
    async with UnitOfWork() as uow:
        yield uow

async def close_engine():
    await engine.dispose()