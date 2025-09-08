from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta

from api.schemas import UserResponse, UserUpdate, MealPlanResponse, ProgressResponse
from core.services.user_service import UserService
from core.services.analytics_service import AnalyticsService
from api.dependencies import get_current_user

router = APIRouter()
user_service = UserService()
analytics_service = AnalyticsService()

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user=Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    return user

@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    user=Depends(get_current_user)
):
    """Обновить информацию пользователя"""
    updated_user = await user_service.update_user(user.id, **user_update.dict(exclude_unset=True))
    return updated_user

@router.get("/me/meal-plan", response_model=List[MealPlanResponse])
async def get_meal_plan(
    week: Optional[int] = None,
    user=Depends(get_current_user)
):
    """Получить план питания"""
    meal_plans = await user_service.get_meal_plans(user.id, week)
    return meal_plans

@router.get("/me/progress", response_model=ProgressResponse)
async def get_progress(
    days: int = 30,
    user=Depends(get_current_user)
):
    """Получить статистику прогресса"""
    progress = await analytics_service.get_user_progress(user.id, days)
    return progress

@router.post("/me/checkin")
async def create_checkin(
    checkin_data: Dict[str, Any],
    user=Depends(get_current_user)
):
    """Создать чек-ин"""
    checkin = await user_service.create_checkin(user.id, **checkin_data)
    return {"status": "success", "checkin_id": checkin.id}