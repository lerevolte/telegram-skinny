from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from contextlib import asynccontextmanager
import logging

from config import settings

logger = logging.getLogger(__name__)

# Создание движка БД
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # True для отладки SQL запросов
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,  # Проверка соединения перед использованием
)

# Создание фабрики сессий
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

@asynccontextmanager
async def get_session():
    """Контекстный менеджер для работы с сессией"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Инициализация БД (создание таблиц)"""
    async with engine.begin() as conn:
        # Импортируем модели, чтобы они были зарегистрированы
        from core.models import User, MealPlan, WorkoutPlan, DailyCheckIn, WeightLog, Payment
        
        # Создаем таблицы
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")

async def drop_db():
    """Удаление всех таблиц (для тестов)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped")