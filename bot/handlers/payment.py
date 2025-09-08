from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery, ContentType
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta

from config import settings
from core.services.payment_service import PaymentService
from core.services.user_service import UserService
from keyboards.inline import get_payment_keyboard, get_subscription_keyboard

router = Router()
payment_service = PaymentService()
user_service = UserService()

@router.callback_query(F.data.in_(["pay_monthly", "pay_quarterly", "pay_yearly"]))
async def process_subscription_choice(callback: CallbackQuery):
    """Обработка выбора подписки"""
    
    subscription_types = {
        "pay_monthly": {
            "type": "monthly",
            "amount": settings.PRICE_MONTHLY,
            "title": "Подписка на месяц",
            "description": "Полный доступ к боту на 30 дней",
            "days": 30
        },
        "pay_quarterly": {
            "type": "quarterly", 
            "amount": settings.PRICE_QUARTERLY,
            "title": "Подписка на 3 месяца",
            "description": "Полный доступ к боту на 90 дней (экономия 20%)",
            "days": 90
        },
        "pay_yearly": {
            "type": "yearly",
            "amount": settings.PRICE_YEARLY,
            "title": "Подписка на год",
            "description": "Полный доступ к боту на 365 дней (экономия 20%)",
            "days": 365
        }
    }
    
    subscription = subscription_types[callback.data]
    
    # Создание инвойса для Telegram Payments
    prices = [
        LabeledPrice(
            label=subscription["title"],
            amount=subscription["amount"]
        )
    ]
    
    await callback.message.answer_invoice(
        title=subscription["title"],
        description=subscription["description"],
        payload=f"{subscription['type']}_{callback.from_user.id}",
        provider_token=settings.YUKASSA_TOKEN,  # или STRIPE_TOKEN
        currency="RUB",
        prices=prices,
        start_parameter="subscription",
        photo_url="https://example.com/fitness-bot-logo.jpg",  # Логотип
        photo_height=512,
        photo_width=512,
        need_name=True,
        need_email=True,
        send_email_to_provider=True
    )
    
    await callback.answer()

@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    """Подтверждение платежа перед оплатой"""
    
    # Проверяем, что платеж корректный
    payload_parts = pre_checkout_query.invoice_payload.split("_")
    subscription_type = payload_parts[0]
    user_id = int(payload_parts[1])
    
    # Проверяем, что пользователь существует
    user = await user_service.get_user(telegram_id=user_id)
    
    if not user:
        await pre_checkout_query.answer(
            ok=False,
            error_message="Пользователь не найден. Начните с команды /start"
        )
        return
    
    # Проверяем, нет ли активной подписки
    if user.status == "active" and user.subscription_end > datetime.utcnow():
        await pre_checkout_query.answer(
            ok=False,
            error_message="У вас уже есть активная подписка"
        )
        return
    
    # Все проверки пройдены
    await pre_checkout_query.answer(ok=True)

@router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def process_successful_payment(message: Message):
    """Обработка успешной оплаты"""
    
    payment = message.successful_payment
    payload_parts = payment.invoice_payload.split("_")
    subscription_type = payload_parts[0]
    user_id = int(payload_parts[1])
    
    # Определяем длительность подписки
    subscription_days = {
        "monthly": 30,
        "quarterly": 90,
        "yearly": 365
    }
    
    days = subscription_days[subscription_type]
    
    # Обновляем статус пользователя
    user = await user_service.get_user(telegram_id=user_id)
    
    # Если у пользователя был триал, отменяем его
    if user.status == "trial":
        start_date = datetime.utcnow()
    else:
        # Если подписка продлевается, добавляем к текущей дате окончания
        start_date = user.subscription_end if user.subscription_end > datetime.utcnow() else datetime.utcnow()
    
    end_date = start_date + timedelta(days=days)
    
    # Сохраняем информацию о платеже
    await payment_service.create_payment(
        user_id=user.id,
        amount=payment.total_amount,
        currency=payment.currency,
        subscription_type=subscription_type,
        provider="telegram_payments",
        provider_payment_id=payment.telegram_payment_charge_id,
        status="succeeded"
    )
    
    # Обновляем подписку пользователя
    await user_service.update_subscription(
        user_id=user.id,
        status="active",
        subscription_type=subscription_type,
        subscription_start=start_date,
        subscription_end=end_date
    )
    
    await message.answer(
        f"🎉 Спасибо за оплату!\n\n"
        f"Твоя подписка активирована до {end_date.strftime('%d.%m.%Y')}.\n"
        f"Теперь тебе доступны все функции бота!\n\n"
        f"Начнем работу над твоей формой! 💪"
    )
    
    # Отправляем главное меню
    from keyboards.reply import get_main_menu_keyboard
    await message.answer(
        "Выбери, что хочешь сделать:",
        reply_markup=get_main_menu_keyboard()
    )

@router.callback_query(F.data == "cancel_subscription")
async def cancel_subscription(callback: CallbackQuery):
    """Отмена подписки"""
    
    user = await user_service.get_user(telegram_id=callback.from_user.id)
    
    if user.status != "active":
        await callback.answer("У вас нет активной подписки", show_alert=True)
        return
    
    # Отменяем автопродление (если реализовано)
    await user_service.cancel_subscription(user.id)
    
    await callback.message.edit_text(
        f"Подписка отменена. Она будет активна до {user.subscription_end.strftime('%d.%m.%Y')}.\n\n"
        "Ты всегда можешь возобновить подписку в любой момент!",
        reply_markup=get_subscription_keyboard()
    )