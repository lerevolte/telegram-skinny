from fastapi import Depends, HTTPException, Header
from typing import Optional

from core.services.user_service import UserService
from core.models import User

user_service = UserService()

async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> User:
    """Получение текущего пользователя по токену"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    # Простая проверка токена (в продакшене использовать JWT)
    # Токен формата: "Bearer {telegram_id}:{secret_hash}"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
        
        telegram_id, secret_hash = token.split(":")
        telegram_id = int(telegram_id)
        
        # В продакшене проверять хеш
        # if not verify_secret_hash(telegram_id, secret_hash):
        #     raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await user_service.get_user(telegram_id=telegram_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
        
    except (ValueError, AttributeError):
        raise HTTPException(status_code=401, detail="Invalid token format")

async def get_admin_user(
    user: User = Depends(get_current_user)
) -> User:
    """Проверка прав администратора"""
    # В продакшене добавить поле is_admin в модель User
    admin_ids = [123456789]  # Telegram ID администраторов
    
    if user.telegram_id not in admin_ids:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return user