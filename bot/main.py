import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import redis.asyncio as redis

from config import settings
from handlers import (
    start_router,
    onboarding_router,
    daily_checkin_router,
    meal_plan_router,
    workout_router,
    payment_router
)
from middlewares.subscription import SubscriptionMiddleware
from core.database import init_db

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def on_startup(bot: Bot):
    """Действия при запуске бота"""
    await init_db()
    await bot.set_webhook(
        url=f"{settings.WEBHOOK_URL}/webhook",
        drop_pending_updates=True
    )
    logger.info("Bot started and webhook set")

async def on_shutdown(bot: Bot):
    """Действия при остановке бота"""
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot stopped")

def create_app():
    """Создание и настройка приложения"""
    # Инициализация бота и диспетчера
    bot = Bot(token=settings.BOT_TOKEN)
    
    # Redis для FSM Storage
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,
        decode_responses=True
    )
    storage = RedisStorage(redis_client)
    
    dp = Dispatcher(storage=storage)
    
    # Регистрация middleware
    dp.message.middleware(SubscriptionMiddleware())
    
    # Регистрация роутеров
    dp.include_router(start_router)
    dp.include_router(onboarding_router)
    dp.include_router(daily_checkin_router)
    dp.include_router(meal_plan_router)
    dp.include_router(workout_router)
    dp.include_router(payment_router)
    
    # Регистрация startup/shutdown хендлеров
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Создание веб-приложения для webhook
    app = web.Application()
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    
    return app, bot, dp

async def main():
    """Основная функция для polling режима (разработка)"""
    bot = Bot(token=settings.BOT_TOKEN)
    
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,
        decode_responses=True
    )
    storage = RedisStorage(redis_client)
    
    dp = Dispatcher(storage=storage)
    
    # Регистрация middleware
    dp.message.middleware(SubscriptionMiddleware())
    
    # Регистрация роутеров
    dp.include_router(start_router)
    dp.include_router(onboarding_router)
    dp.include_router(daily_checkin_router)
    dp.include_router(meal_plan_router)
    dp.include_router(workout_router)
    dp.include_router(payment_router)
    
    # Инициализация БД
    await init_db()
    
    # Запуск polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    if settings.USE_WEBHOOK:
        # Production режим с webhook
        app, bot, dp = create_app()
        web.run_app(app, host="0.0.0.0", port=settings.WEBHOOK_PORT)
    else:
        # Development режим с polling
        asyncio.run(main())