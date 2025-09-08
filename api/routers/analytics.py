from fastapi import APIRouter, Depends
from typing import Dict, Any
from datetime import datetime, timedelta

from core.services.analytics_service import AnalyticsService
from api.dependencies import get_admin_user

router = APIRouter()
analytics_service = AnalyticsService()

@router.get("/overview")
async def get_analytics_overview(admin=Depends(get_admin_user)):
    """Общая аналитика по боту"""
    return await analytics_service.get_overview()

@router.get("/users/active")
async def get_active_users(
    days: int = 7,
    admin=Depends(get_admin_user)
):
    """Активные пользователи за период"""
    return await analytics_service.get_active_users(days)

@router.get("/revenue")
async def get_revenue_stats(
    start_date: datetime = None,
    end_date: datetime = None,
    admin=Depends(get_admin_user)
):
    """Статистика по доходам"""
    if not start_date:
        start_date = datetime.now() - timedelta(days=30)
    if not end_date:
        end_date = datetime.now()
    
    return await analytics_service.get_revenue_stats(start_date, end_date)

@router.get("/retention")
async def get_retention_stats(admin=Depends(get_admin_user)):
    """Статистика удержания пользователей"""
    return await analytics_service.get_retention_stats()