from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

from api.schemas import UserResponse, BroadcastMessage
from core.services.admin_service import AdminService
from api.dependencies import get_admin_user

router = APIRouter()
admin_service = AdminService()

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    admin=Depends(get_admin_user)
):
    """Получить список всех пользователей"""
    users = await admin_service.get_users(status, limit, offset)
    return users

@router.post("/broadcast")
async def send_broadcast(
    message: BroadcastMessage,
    admin=Depends(get_admin_user)
):
    """Отправить рассылку всем пользователям"""
    result = await admin_service.send_broadcast(
        message.text,
        message.target_status,
        message.include_photo
    )
    return result

@router.post("/users/{user_id}/ban")
async def ban_user(
    user_id: int,
    reason: str,
    admin=Depends(get_admin_user)
):
    """Заблокировать пользователя"""
    result = await admin_service.ban_user(user_id, reason)
    return {"status": "success", "user_id": user_id}

@router.post("/users/{user_id}/unban")
async def unban_user(
    user_id: int,
    admin=Depends(get_admin_user)
):
    """Разблокировать пользователя"""
    result = await admin_service.unban_user(user_id)
    return {"status": "success", "user_id": user_id}

@router.post("/generate-promo")
async def generate_promo_code(
    discount_percent: int,
    max_uses: int,
    expires_days: int,
    admin=Depends(get_admin_user)
):
    """Сгенерировать промокод"""
    promo_code = await admin_service.generate_promo_code(
        discount_percent,
        max_uses,
        expires_days
    )
    return {"promo_code": promo_code}