from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, date
from sqlalchemy import select, and_, desc

from core.database import get_session
from core.models import User, WorkoutPlan

class WorkoutService:
    """Сервис для работы с тренировками"""
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по telegram_id"""
        async with get_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()
    
    async def get_today_workout(self, user_id: int) -> Optional[WorkoutPlan]:
        """Получить тренировку на сегодня"""
        async with get_session() as session:
            # Определяем номер дня недели (1-7)
            today = datetime.now().weekday() + 1
            
            # Получаем текущую неделю (можно вычислять на основе даты начала)
            current_week = 1  # Упрощенно для MVP
            
            result = await session.execute(
                select(WorkoutPlan).where(
                    and_(
                        WorkoutPlan.user_id == user_id,
                        WorkoutPlan.week_number == current_week,
                        WorkoutPlan.day_number == today
                    )
                )
            )
            return result.scalar_one_or_none()
    
    async def get_workout_by_id(self, workout_id: int) -> Optional[WorkoutPlan]:
        """Получить тренировку по ID"""
        async with get_session() as session:
            return await session.get(WorkoutPlan, workout_id)
    
    async def mark_workout_completed(self, workout_id: int) -> WorkoutPlan:
        """Отметить тренировку как выполненную"""
        async with get_session() as session:
            workout = await session.get(WorkoutPlan, workout_id)
            
            if workout:
                workout.completed = True
                workout.completed_at = datetime.utcnow()
                
                await session.commit()
                await session.refresh(workout)
            
            return workout
    
    async def get_workout_history(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[WorkoutPlan]:
        """Получить историю тренировок"""
        async with get_session() as session:
            result = await session.execute(
                select(WorkoutPlan)
                .where(WorkoutPlan.user_id == user_id)
                .order_by(desc(WorkoutPlan.created_at))
                .limit(limit)
            )
            return result.scalars().all()
    
    async def generate_workout_plan(
        self,
        user_id: int,
        weeks: int = 4
    ) -> List[WorkoutPlan]:
        """Генерация плана тренировок"""
        async with get_session() as session:
            user = await session.get(User, user_id)
            
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            workouts = []
            
            # Определяем уровень сложности
            if user.activity_level in ["sedentary", "light"]:
                difficulty = "beginner"
                workout_days = [1, 3, 5]  # Пн, Ср, Пт
            elif user.activity_level == "moderate":
                difficulty = "intermediate"
                workout_days = [1, 2, 4, 5]  # Пн, Вт, Чт, Пт
            else:
                difficulty = "advanced"
                workout_days = [1, 2, 3, 4, 5, 6]  # Пн-Сб
            
            for week in range(1, weeks + 1):
                for day in range(1, 8):
                    if day in workout_days:
                        # Чередуем типы тренировок
                        if week % 2 == 0:
                            workout_type = "strength" if day % 2 == 1 else "cardio"
                        else:
                            workout_type = "cardio" if day % 2 == 1 else "strength"
                        
                        exercises = self._generate_exercises(
                            workout_type,
                            difficulty,
                            user.goal
                        )
                        
                        workout = WorkoutPlan(
                            user_id=user_id,
                            week_number=week,
                            day_number=day,
                            workout_type=workout_type,
                            duration_minutes=30 if difficulty == "beginner" else 45,
                            difficulty=difficulty,
                            exercises=exercises,
                            calories_burned=self._estimate_calories(
                                workout_type,
                                difficulty,
                                user.weight
                            )
                        )
                        
                        session.add(workout)
                        workouts.append(workout)
                    else:
                        # День отдыха
                        workout = WorkoutPlan(
                            user_id=user_id,
                            week_number=week,
                            day_number=day,
                            workout_type="rest",
                            duration_minutes=0,
                            difficulty=difficulty,
                            exercises=[],
                            calories_burned=0
                        )
                        session.add(workout)
            
            await session.commit()
            return workouts
    
    def _generate_exercises(
        self,
        workout_type: str,
        difficulty: str,
        goal: str
    ) -> List[Dict[str, Any]]:
        """Генерация упражнений для тренировки"""
        
        exercises = []
        
        if workout_type == "strength":
            if difficulty == "beginner":
                exercises = [
                    {
                        "name": "Приседания",
                        "sets": 3,
                        "reps": 12,
                        "rest": 60,
                        "description": "Приседай до параллели бедер с полом",
                        "tips": "Держи спину прямо, колени не выходят за носки"
                    },
                    {
                        "name": "Отжимания от колен",
                        "sets": 3,
                        "reps": 10,
                        "rest": 60,
                        "description": "Отжимания с упором на колени",
                        "tips": "Держи корпус прямым, опускайся медленно"
                    },
                    {
                        "name": "Планка",
                        "duration": 30,
                        "sets": 3,
                        "rest": 45,
                        "description": "Статическое удержание положения",
                        "tips": "Не прогибай поясницу, дыши ровно"
                    },
                    {
                        "name": "Выпады",
                        "sets": 3,
                        "reps": 10,
                        "rest": 60,
                        "description": "Попеременные выпады вперед",
                        "tips": "Колено не касается пола, держи баланс"
                    }
                ]
            elif difficulty == "intermediate":
                exercises = [
                    {
                        "name": "Приседания с прыжком",
                        "sets": 4,
                        "reps": 15,
                        "rest": 45,
                        "description": "Приседание с выпрыгиванием вверх"
                    },
                    {
                        "name": "Отжимания",
                        "sets": 4,
                        "reps": 15,
                        "rest": 45,
                        "description": "Классические отжимания"
                    },
                    {
                        "name": "Берпи",
                        "sets": 3,
                        "reps": 10,
                        "rest": 60,
                        "description": "Комплексное упражнение"
                    },
                    {
                        "name": "Альпинист",
                        "duration": 45,
                        "sets": 3,
                        "rest": 45,
                        "description": "Бег в упоре лежа"
                    },
                    {
                        "name": "Планка",
                        "duration": 60,
                        "sets": 3,
                        "rest": 45
                    }
                ]
            else:  # advanced
                exercises = [
                    {
                        "name": "Приседания на одной ноге",
                        "sets": 4,
                        "reps": 10,
                        "rest": 60
                    },
                    {
                        "name": "Отжимания с хлопком",
                        "sets": 4,
                        "reps": 12,
                        "rest": 60
                    },
                    {
                        "name": "Берпи с отжиманием",
                        "sets": 4,
                        "reps": 15,
                        "rest": 60
                    },
                    {
                        "name": "Прыжки на тумбу",
                        "sets": 4,
                        "reps": 12,
                        "rest": 60
                    },
                    {
                        "name": "Планка с подъемом ног",
                        "duration": 90,
                        "sets": 3,
                        "rest": 45
                    }
                ]
        
        elif workout_type == "cardio":
            if difficulty == "beginner":
                exercises = [
                    {
                        "name": "Ходьба на месте",
                        "duration": 300,
                        "description": "Разминка"
                    },
                    {
                        "name": "Прыжки звездочкой",
                        "duration": 30,
                        "sets": 3,
                        "rest": 30
                    },
                    {
                        "name": "Высокие колени",
                        "duration": 30,
                        "sets": 3,
                        "rest": 30
                    },
                    {
                        "name": "Бег на месте",
                        "duration": 60,
                        "sets": 3,
                        "rest": 45
                    }
                ]
            else:
                exercises = [
                    {
                        "name": "Интервальный бег",
                        "duration": 30,
                        "sets": 8,
                        "rest": 30,
                        "description": "30 сек быстро, 30 сек отдых"
                    },
                    {
                        "name": "Берпи",
                        "sets": 4,
                        "reps": 15,
                        "rest": 45
                    },
                    {
                        "name": "Прыжки на скакалке",
                        "duration": 120,
                        "sets": 3,
                        "rest": 60
                    }
                ]
        
        return exercises
    
    def _estimate_calories(
        self,
        workout_type: str,
        difficulty: str,
        weight: float
    ) -> int:
        """Оценка сожженных калорий"""
        # Упрощенная формула
        base_calories = {
            "strength": 5,  # ккал/мин
            "cardio": 8,
            "mixed": 6,
            "rest": 0
        }
        
        difficulty_multiplier = {
            "beginner": 0.8,
            "intermediate": 1.0,
            "advanced": 1.3
        }
        
        duration = 30 if difficulty == "beginner" else 45
        
        calories = (
            base_calories.get(workout_type, 5) *
            duration *
            difficulty_multiplier.get(difficulty, 1.0) *
            (weight / 70)  # Корректировка на вес
        )
        
        return int(calories)