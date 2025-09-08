from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_

from core.database import get_session
from core.models import User, MealPlan, DailyCheckIn, WeightLog, UserStatus

class UserService:
    """Сервис для работы с пользователями"""
    
    async def get_or_create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> User:
        """Получить или создать пользователя"""
        async with get_session() as session:
            # Проверяем существование
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                # Обновляем последнюю активность
                user.last_activity = datetime.utcnow()
                await session.commit()
                return user
            
            # Создаем нового пользователя
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name or "Пользователь",
                last_name=last_name,
                status=UserStatus.TRIAL,
                trial_start=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            return user
    
    async def get_user(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по telegram_id"""
        async with get_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()
    
    async def update_user_profile(
        self,
        telegram_id: int,
        **kwargs
    ) -> User:
        """Обновить профиль пользователя"""
        async with get_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise ValueError(f"User with telegram_id {telegram_id} not found")
            
            # Обновляем поля
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            user.updated_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(user)
            
            return user
    
    async def update_nutrition_targets(
        self,
        user_id: int,
        nutrition_data: Dict[str, int]
    ) -> User:
        """Обновить целевые показатели питания"""
        async with get_session() as session:
            user = await session.get(User, user_id)
            
            if not user:
                raise ValueError(f"User with id {user_id} not found")
            
            user.bmr = nutrition_data.get("bmr")
            user.tdee = nutrition_data.get("tdee")
            user.daily_calories = nutrition_data["calories"]
            user.daily_protein = nutrition_data["protein"]
            user.daily_carbs = nutrition_data["carbs"]
            user.daily_fats = nutrition_data["fats"]
            
            await session.commit()
            await session.refresh(user)
            
            return user
    
    async def update_subscription(
        self,
        user_id: int,
        status: str,
        subscription_type: str,
        subscription_start: datetime,
        subscription_end: datetime
    ) -> User:
        """Обновить подписку пользователя"""
        async with get_session() as session:
            user = await session.get(User, user_id)
            
            if not user:
                raise ValueError(f"User with id {user_id} not found")
            
            user.status = UserStatus(status)
            user.subscription_type = subscription_type
            user.subscription_start = subscription_start
            user.subscription_end = subscription_end
            user.updated_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(user)
            
            return user
    
    async def cancel_subscription(self, user_id: int) -> User:
        """Отменить подписку (отключить автопродление)"""
        async with get_session() as session:
            user = await session.get(User, user_id)
            
            if not user:
                raise ValueError(f"User with id {user_id} not found")
            
            user.status = UserStatus.CANCELLED
            user.updated_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(user)
            
            return user
    
    async def get_meal_plans(
        self,
        user_id: int,
        week: Optional[int] = None
    ) -> List[MealPlan]:
        """Получить планы питания пользователя"""
        async with get_session() as session:
            query = select(MealPlan).where(
                MealPlan.user_id == user_id,
                MealPlan.is_active == True
            )
            
            if week:
                query = query.where(MealPlan.week_number == week)
            
            query = query.order_by(MealPlan.day_number)
            
            result = await session.execute(query)
            return result.scalars().all()
    
    async def create_checkin(
        self,
        user_id: int,
        **checkin_data
    ) -> DailyCheckIn:
        """Создать чек-ин"""
        async with get_session() as session:
            checkin = DailyCheckIn(
                user_id=user_id,
                date=datetime.utcnow(),
                **checkin_data
            )
            
            session.add(checkin)
            await session.commit()
            await session.refresh(checkin)
            
            return checkin
    
    async def log_weight(
        self,
        telegram_id: int,
        weight: float
    ) -> WeightLog:
        """Записать вес пользователя"""
        async with get_session() as session:
            # Получаем пользователя
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise ValueError(f"User with telegram_id {telegram_id} not found")
            
            # Создаем запись веса
            weight_log = WeightLog(
                user_id=user.id,
                weight=weight,
                date=datetime.utcnow()
            )
            
            # Обновляем текущий вес пользователя
            user.weight = weight
            user.updated_at = datetime.utcnow()
            
            session.add(weight_log)
            await session.commit()
            await session.refresh(weight_log)
            
            return weight_log