from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from datetime import datetime

from core.services.user_service import UserService

class SubscriptionMiddleware(BaseMiddleware):
    """Middleware для проверки подписки"""
    
    # Команды, доступные без подписки
    FREE_COMMANDS = [
        "/start",
        "/help",
        "/about",
        "/subscribe",
        "/support"
    ]
    
    # Callback, доступные без подписки
    FREE_CALLBACKS = [
        "start_trial",
        "buy_subscription",
        "pay_monthly",
        "pay_quarterly",
        "pay_yearly",
        "about",
        "support"
    ]
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        
        user_service = UserService()
        
        # Получаем пользователя
        user_id = event.from_user.id
        user = await user_service.get_user(telegram_id=user_id)
        
        # Если пользователя нет, пропускаем (обработается в start)
        if not user:
            return await handler(event, data)
        
        # Проверяем тип события
        if isinstance(event, Message):
            # Проверяем, является ли это бесплатной командой
            if event.text and event.text.split()[0] in self.FREE_COMMANDS:
                return await handler(event, data)
            
            # Проверяем подписку
            if not await self._check_subscription(user):
                await event.answer(
                    "⚠️ Для использования этой функции нужна подписка.\n\n"
                    "Оформи бесплатный пробный период на 7 дней или купи подписку!",
                    reply_markup=get_subscription_keyboard()
                )
                return
        
        elif isinstance(event, CallbackQuery):
            # Проверяем, является ли это бесплатным callback
            if event.data in self.FREE_CALLBACKS:
                return await handler(event, data)
            
            # Проверяем подписку
            if not await self._check_subscription(user):
                await event.answer(
                    "⚠️ Для использования этой функции нужна подписка.",
                    show_alert=True
                )
                return
        
        # Добавляем пользователя в data для использования в хендлерах
        data["user"] = user
        
        return await handler(event, data)
    
    async def _check_subscription(self, user) -> bool:
        """Проверка активности подписки"""
        
        # Проверяем триальный период
        if user.status == "trial":
            trial_end = user.trial_start + timedelta(days=settings.TRIAL_DAYS)
            if datetime.utcnow() < trial_end:
                return True
            else:
                # Триал закончился, обновляем статус
                await UserService().update_user_status(user.id, "expired")
                return False
        
        # Проверяем активную подписку
        if user.status == "active":
            if datetime.utcnow() < user.subscription_end:
                return True
            else:
                # Подписка закончилась
                await UserService().update_user_status(user.id, "expired")
                return False
        
        return False