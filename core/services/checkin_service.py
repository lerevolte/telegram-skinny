from typing import Dict, Any, Optional
from datetime import datetime, date
from sqlalchemy import select, and_

from core.database import get_session
from core.models import DailyCheckIn, User

class CheckInService:
    """Сервис для работы с чек-инами"""
    
    async def save_morning_checkin(
        self,
        user_id: int,
        morning_weight: Optional[float] = None,
        sleep_hours: Optional[float] = None,
        mood: Optional[str] = None
    ) -> DailyCheckIn:
        """Сохранить утренний чек-ин"""
        async with get_session() as session:
            # Проверяем, есть ли уже чек-ин за сегодня
            today = date.today()
            result = await session.execute(
                select(DailyCheckIn).where(
                    and_(
                        DailyCheckIn.user_id == user_id,
                        DailyCheckIn.date >= today,
                        DailyCheckIn.date < today + timedelta(days=1)
                    )
                )
            )
            checkin = result.scalar_one_or_none()
            
            if checkin:
                # Обновляем существующий
                if morning_weight:
                    checkin.morning_weight = morning_weight
                if sleep_hours:
                    checkin.sleep_hours = sleep_hours
                if mood:
                    checkin.mood = mood
            else:
                # Создаем новый
                checkin = DailyCheckIn(
                    user_id=user_id,
                    date=datetime.utcnow(),
                    morning_weight=morning_weight,
                    sleep_hours=sleep_hours,
                    mood=mood
                )
                session.add(checkin)
            
            await session.commit()
            await session.refresh(checkin)
            
            return checkin
    
    async def save_food_log(
        self,
        user_id: int,
        meal_type: str,
        food_photo: Optional[str] = None,
        estimated_calories: Optional[int] = None
    ) -> DailyCheckIn:
        """Сохранить лог еды"""
        async with get_session() as session:
            # Получаем или создаем чек-ин за сегодня
            today = date.today()
            result = await session.execute(
                select(DailyCheckIn).where(
                    and_(
                        DailyCheckIn.user_id == user_id,
                        DailyCheckIn.date >= today,
                        DailyCheckIn.date < today + timedelta(days=1)
                    )
                )
            )
            checkin = result.scalar_one_or_none()
            
            if not checkin:
                checkin = DailyCheckIn(
                    user_id=user_id,
                    date=datetime.utcnow()
                )
                session.add(checkin)
            
            # Сохраняем фото в соответствующее поле
            if meal_type == "breakfast":
                checkin.breakfast_photo = food_photo
            elif meal_type == "lunch":
                checkin.lunch_photo = food_photo
            elif meal_type == "dinner":
                checkin.dinner_photo = food_photo
            elif meal_type == "snack":
                snack_photos = checkin.snack_photos or []
                snack_photos.append(food_photo)
                checkin.snack_photos = snack_photos
            
            # Обновляем оценку калорий
            if estimated_calories:
                current_calories = checkin.estimated_calories or 0
                checkin.estimated_calories = current_calories + estimated_calories
            
            await session.commit()
            await session.refresh(checkin)
            
            return checkin
    
    async def log_weight(
        self,
        telegram_id: int,
        weight: float
    ) -> WeightLog:
        """Записать вес"""
        from core.services.user_service import UserService
        user_service = UserService()
        return await user_service.log_weight(telegram_id, weight)