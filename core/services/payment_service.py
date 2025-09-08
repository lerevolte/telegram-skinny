from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from core.database import get_session
from core.models import Payment, User

class PaymentService:
    """Сервис для работы с платежами"""
    
    async def create_payment(
        self,
        user_id: int,
        amount: int,
        currency: str,
        subscription_type: str,
        provider: str,
        provider_payment_id: str,
        status: str = "pending"
    ) -> Payment:
        """Создание записи о платеже"""
        async with get_session() as session:
            payment = Payment(
                user_id=user_id,
                amount=amount,
                currency=currency,
                subscription_type=subscription_type,
                provider=provider,
                provider_payment_id=provider_payment_id,
                status=status,
                paid_at=datetime.utcnow() if status == "succeeded" else None
            )
            
            session.add(payment)
            await session.commit()
            await session.refresh(payment)
            
            return payment
    
    async def get_payment(self, payment_id: int) -> Optional[Payment]:
        """Получение платежа по ID"""
        async with get_session() as session:
            result = await session.execute(
                select(Payment).where(Payment.id == payment_id)
            )
            return result.scalar_one_or_none()
    
    async def get_user_payments(self, user_id: int) -> list[Payment]:
        """Получение всех платежей пользователя"""
        async with get_session() as session:
            result = await session.execute(
                select(Payment)
                .where(Payment.user_id == user_id)
                .order_by(Payment.created_at.desc())
            )
            return result.scalars().all()
    
    async def update_payment_status(
        self,
        provider_payment_id: str,
        status: str
    ) -> Optional[Payment]:
        """Обновление статуса платежа"""
        async with get_session() as session:
            result = await session.execute(
                select(Payment).where(
                    Payment.provider_payment_id == provider_payment_id
                )
            )
            payment = result.scalar_one_or_none()
            
            if payment:
                payment.status = status
                if status == "succeeded":
                    payment.paid_at = datetime.utcnow()
                
                await session.commit()
                await session.refresh(payment)
            
            return payment
    
    async def process_webhook(self, provider: str, data: Dict[str, Any]) -> bool:
        """Обработка вебхука от платежной системы"""
        
        if provider == "yukassa":
            return await self._process_yukassa_webhook(data)
        elif provider == "stripe":
            return await self._process_stripe_webhook(data)
        
        return False
    
    async def _process_yukassa_webhook(self, data: Dict[str, Any]) -> bool:
        """Обработка вебхука ЮKassa"""
        # Пример обработки вебхука ЮKassa
        event = data.get("event")
        
        if event == "payment.succeeded":
            payment_id = data["object"]["id"]
            await self.update_payment_status(payment_id, "succeeded")
            
            # Активируем подписку пользователя
            payment = await self.get_payment_by_provider_id(payment_id)
            if payment:
                from core.services.user_service import UserService
                user_service = UserService()
                await user_service.activate_subscription(payment.user_id)
            
            return True
        
        elif event == "payment.canceled":
            payment_id = data["object"]["id"]
            await self.update_payment_status(payment_id, "failed")
            return True
        
        return False
    
    async def _process_stripe_webhook(self, data: Dict[str, Any]) -> bool:
        """Обработка вебхука Stripe"""
        # Похожая логика для Stripe
        pass