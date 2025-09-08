from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any
import hmac
import hashlib

from core.services.payment_service import PaymentService
from config import settings

router = APIRouter()
payment_service = PaymentService()

@router.post("/telegram")
async def telegram_webhook(request: Request):
    """Вебхук для Telegram (если используется вместо polling)"""
    data = await request.json()
    # Обработка происходит в aiogram
    return {"ok": True}

@router.post("/yukassa")
async def yukassa_webhook(request: Request):
    """Вебхук для обработки платежей ЮKassa"""
    data = await request.json()
    
    # Проверка подписи (важно для безопасности!)
    signature = request.headers.get("X-Yookassa-Signature")
    if not verify_yukassa_signature(data, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Обработка события
    result = await payment_service.process_webhook("yukassa", data)
    
    if result:
        return {"status": "success"}
    else:
        raise HTTPException(status_code=400, detail="Failed to process webhook")

@router.post("/stripe")
async def stripe_webhook(request: Request):
    """Вебхук для обработки платежей Stripe"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        import stripe
        stripe.api_key = settings.STRIPE_TOKEN
        
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        
        result = await payment_service.process_webhook("stripe", event)
        
        if result:
            return {"status": "success"}
        else:
            raise HTTPException(status_code=400, detail="Failed to process webhook")
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

def verify_yukassa_signature(data: Dict[str, Any], signature: str) -> bool:
    """Проверка подписи ЮKassa"""
    # Реализация проверки подписи
    # https://yookassa.ru/developers/using-api/webhooks#webhook-notification-validation
    secret = settings.YUKASSA_WEBHOOK_SECRET
    message = f"{data['event']}&{data['object']['id']}"
    expected_signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)