from celery import shared_task
from typing import Dict, Any, List
from datetime import datetime, timedelta
import asyncio
from aiogram import Bot

from core.database import get_session
from core.models import User, MealPlan, DailyCheckIn, WeightLog
from core.services.nutrition_service import NutritionService
from core.services.notification_service import NotificationService
from config import settings

# Инициализация сервисов
nutrition_service = NutritionService()
notification_service = NotificationService()

@shared_task
def generate_meal_plan_task(user_id: int):
    """Генерация плана питания для пользователя"""
    try:
        asyncio.run(_generate_meal_plan(user_id))
        return {"status": "success", "user_id": user_id}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def _generate_meal_plan(user_id: int):
    """Асинхронная генерация плана питания"""
    async with get_session() as session:
        # Получаем данные пользователя
        user = await session.get(User, user_id)
        if not user:
            return
        
        user_data = {
            "daily_calories": user.daily_calories,
            "daily_protein": user.daily_protein,
            "daily_carbs": user.daily_carbs,
            "daily_fats": user.daily_fats,
            "meals_per_day": user.meals_per_day,
            "dietary_restrictions": user.dietary_restrictions,
            "budget": user.budget
        }
        
        # Генерируем план на неделю
        meal_plans = await nutrition_service.generate_meal_plan(user_data, days=7)
        
        # Сохраняем в БД
        for plan in meal_plans:
            meal_plan = MealPlan(
                user_id=user_id,
                week_number=1,  # Номер недели
                day_number=plan["day"],
                breakfast=plan["meals"][0],
                lunch=plan["meals"][1],
                dinner=plan["meals"][2],
                snack=plan["meals"][3] if len(plan["meals"]) > 3 else None,
                total_calories=plan["total_calories"],
                total_protein=plan["total_protein"],
                total_carbs=plan["total_carbs"],
                total_fats=plan["total_fats"],
                shopping_list=self._generate_shopping_list(plan["meals"])
            )
            session.add(meal_plan)
        
        await session.commit()
        
        # Отправляем уведомление пользователю
        bot = Bot(token=settings.BOT_TOKEN)
        await bot.send_message(
            user.telegram_id,
            "🎉 Твой персональный план питания на неделю готов!\n"
            "Посмотреть можно в разделе «📊 Мой план»"
        )
        await bot.session.close()

def _generate_shopping_list(meals: List[Dict]) -> List[Dict]:
    """Генерация списка покупок из блюд"""
    shopping_list = {}
    
    for meal in meals:
        for ingredient in meal.get("ingredients", []):
            name = ingredient["name"]
            amount = ingredient["amount"]
            
            if name in shopping_list:
                # Суммируем количество
                shopping_list[name] += amount
            else:
                shopping_list[name] = amount
    
    return [{"name": k, "amount": v} for k, v in shopping_list.items()]

@shared_task
def send_morning_reminder():
    """Отправка утренних напоминаний"""
    asyncio.run(_send_morning_reminders())
    return {"status": "success", "type": "morning_reminder"}

async def _send_morning_reminders():
    """Асинхронная отправка утренних напоминаний"""
    async with get_session() as session:
        # Получаем активных пользователей
        users = await session.execute(
            select(User).where(
                User.status.in_(["trial", "active"])
            )
        )
        users = users.scalars().all()
        
        bot = Bot(token=settings.BOT_TOKEN)
        
        for user in users:
            try:
                await bot.send_message(
                    user.telegram_id,
                    "☀️ Доброе утро!\n\n"
                    "Не забудь:\n"
                    "• Взвеситься и записать вес\n"
                    "• Выпить стакан воды\n"
                    "• Проверить план на сегодня\n\n"
                    "Нажми /checkin для утреннего чек-ина!"
                )
            except Exception as e:
                print(f"Error sending morning reminder to {user.telegram_id}: {e}")
        
        await bot.session.close()

@shared_task
def send_workout_reminder():
    """Напоминание о тренировке"""
    asyncio.run(_send_workout_reminders())
    return {"status": "success", "type": "workout_reminder"}

async def _send_workout_reminders():
    """Асинхронная отправка напоминаний о тренировке"""
    async with get_session() as session:
        # Получаем пользователей с тренировкой сегодня
        today = datetime.now().weekday() + 1  # 1-7
        
        users = await session.execute(
            select(User).where(
                User.status.in_(["trial", "active"])
            )
        )
        users = users.scalars().all()
        
        bot = Bot(token=settings.BOT_TOKEN)
        
        for user in users:
            # Проверяем, есть ли тренировка сегодня
            if today in [1, 3, 5]:  # Пн, Ср, Пт
                try:
                    await bot.send_message(
                        user.telegram_id,
                        "💪 Время тренировки!\n\n"
                        "Сегодня у тебя запланирована тренировка.\n"
                        "Всего 20-30 минут для твоей формы!\n\n"
                        "Готов начать? Нажми «🏋️ Тренировка» в меню"
                    )
                except Exception as e:
                    print(f"Error sending workout reminder to {user.telegram_id}: {e}")
        
        await bot.session.close()

@shared_task
def send_evening_reminder():
    """Вечернее напоминание о чек-ине"""
    asyncio.run(_send_evening_reminders())
    return {"status": "success", "type": "evening_reminder"}

async def _send_evening_reminders():
    """Асинхронная отправка вечерних напоминаний"""
    async with get_session() as session:
        users = await session.execute(
            select(User).where(
                User.status.in_(["trial", "active"])
            )
        )
        users = users.scalars().all()
        
        bot = Bot(token=settings.BOT_TOKEN)
        
        for user in users:
            # Проверяем, был ли сегодня чек-ин
            today_checkin = await session.execute(
                select(DailyCheckIn).where(
                    DailyCheckIn.user_id == user.id,
                    DailyCheckIn.date >= datetime.now().date()
                )
            )
            
            if not today_checkin.scalar_one_or_none():
                try:
                    await bot.send_message(
                        user.telegram_id,
                        "🌙 Как прошел твой день?\n\n"
                        "Не забудь:\n"
                        "• Отправить фото ужина\n"
                        "• Записать количество воды\n"
                        "• Отметить выполненную тренировку\n\n"
                        "Нажми /checkin для вечернего отчета!"
                    )
                except Exception as e:
                    print(f"Error sending evening reminder to {user.telegram_id}: {e}")
        
        await bot.session.close()

@shared_task
def check_expiring_subscriptions():
    """Проверка истекающих подписок"""
    asyncio.run(_check_expiring_subscriptions())
    return {"status": "success", "type": "subscription_check"}

async def _check_expiring_subscriptions():
    """Асинхронная проверка подписок"""
    async with get_session() as session:
        # Ищем подписки, истекающие через 3 дня
        expiry_date = datetime.now() + timedelta(days=3)
        
        users = await session.execute(
            select(User).where(
                User.status == "active",
                User.subscription_end <= expiry_date,
                User.subscription_end > datetime.now()
            )
        )
        users = users.scalars().all()
        
        bot = Bot(token=settings.BOT_TOKEN)
        
        for user in users:
            days_left = (user.subscription_end - datetime.now()).days
            
            try:
                await bot.send_message(
                    user.telegram_id,
                    f"⚠️ Твоя подписка заканчивается через {days_left} дн.\n\n"
                    "Продли подписку сейчас, чтобы не потерять:\n"
                    "• Персональные планы питания\n"
                    "• Адаптивные тренировки\n"
                    "• Анализ прогресса\n\n"
                    "Нажми /subscribe для продления"
                )
            except Exception as e:
                print(f"Error sending subscription reminder to {user.telegram_id}: {e}")
        
        await bot.session.close()

@shared_task
def analyze_user_progress(user_id: int = None):
    """Анализ прогресса пользователя и адаптация плана"""
    asyncio.run(_analyze_progress(user_id))
    return {"status": "success", "type": "progress_analysis"}

async def _analyze_progress(user_id: int = None):
    """Асинхронный анализ прогресса"""
    async with get_session() as session:
        if user_id:
            users = [await session.get(User, user_id)]
        else:
            # Анализируем всех активных пользователей
            result = await session.execute(
                select(User).where(
                    User.status.in_(["trial", "active"])
                )
            )
            users = result.scalars().all()
        
        bot = Bot(token=settings.BOT_TOKEN)
        
        for user in users:
            if not user:
                continue
            
            # Получаем последние 7 дней взвешиваний
            weight_logs = await session.execute(
                select(WeightLog).where(
                    WeightLog.user_id == user.id
                ).order_by(WeightLog.date.desc()).limit(7)
            )
            weight_logs = weight_logs.scalars().all()
            
            if len(weight_logs) >= 3:
                # Анализируем тренд веса
                weights = [log.weight for log in weight_logs]
                avg_change = (weights[0] - weights[-1]) / len(weights)
                
                message = None
                
                # Проверяем прогресс относительно цели
                if user.goal == "weight_loss":
                    if avg_change < -0.2:  # Теряет больше 200г в день
                        message = "⚠️ Ты теряешь вес слишком быстро. Я увеличу калории на 100 ккал."
                        user.daily_calories += 100
                    elif avg_change > 0.1:  # Набирает вес
                        message = "📊 Вес не снижается. Уменьшу калории на 100 ккал и добавлю кардио."
                        user.daily_calories -= 100
                    elif -0.2 <= avg_change <= -0.05:  # Оптимальная потеря
                        message = "✅ Отличный прогресс! Продолжай в том же духе!"
                
                elif user.goal == "muscle_gain":
                    if avg_change < 0.05:  # Не набирает
                        message = "📈 Нужно больше калорий для роста мышц. Добавлю 150 ккал."
                        user.daily_calories += 150
                    elif avg_change > 0.3:  # Слишком быстрый набор
                        message = "⚠️ Набор веса слишком быстрый. Уменьшу калории на 100 ккал."
                        user.daily_calories -= 100
                
                if message:
                    await session.commit()
                    
                    try:
                        await bot.send_message(user.telegram_id, message)
                    except Exception as e:
                        print(f"Error sending progress update to {user.telegram_id}: {e}")
        
        await bot.session.close()

@shared_task
def generate_weekly_meal_plans():
    """Генерация планов питания на следующую неделю"""
    asyncio.run(_generate_weekly_plans())
    return {"status": "success", "type": "weekly_generation"}

async def _generate_weekly_plans():
    """Асинхронная генерация недельных планов"""
    async with get_session() as session:
        users = await session.execute(
            select(User).where(
                User.status.in_(["trial", "active"])
            )
        )
        users = users.scalars().all()
        
        for user in users:
            # Запускаем генерацию для каждого пользователя
            generate_meal_plan_task.delay(user.id)
    
    return {"generated_for": len(users)}