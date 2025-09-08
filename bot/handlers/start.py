from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from keyboards.inline import get_start_keyboard, get_subscription_keyboard
from core.services.user_service import UserService
from states.user_states import OnboardingStates

router = Router()
user_service = UserService()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start"""
    user = await user_service.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    welcome_text = (
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Я твой персональный фитнес-помощник «Форма за 90 дней».\n\n"
        "Я помогу тебе:\n"
        "✅ Создать персональный план питания\n"
        "✅ Подобрать эффективные тренировки\n"
        "✅ Отслеживать прогресс каждый день\n"
        "✅ Адаптировать план под твои результаты\n\n"
        "Готов начать трансформацию?"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_start_keyboard(has_subscription=user.status == "active")
    )

@router.callback_query(F.data == "start_trial")
async def start_trial(callback: CallbackQuery, state: FSMContext):
    """Начало пробного периода"""
    await callback.message.edit_text(
        "Отлично! Начнем с быстрого опроса, чтобы создать твой персональный план.\n\n"
        "Это займет всего 2-3 минуты.",
        reply_markup=None
    )
    
    await callback.message.answer("Укажи свой пол:", reply_markup=get_gender_keyboard())
    await state.set_state(OnboardingStates.gender)

@router.callback_query(F.data == "buy_subscription")
async def show_subscription_plans(callback: CallbackQuery):
    """Показать планы подписки"""
    text = (
        "💎 Выбери подходящий план:\n\n"
        "📅 **Месяц** — 1 290 ₽\n"
        "Полный доступ на 30 дней\n\n"
        "📅 **3 месяца** — 3 490 ₽ (экономия 380 ₽)\n"
        "Лучший выбор для видимых результатов\n\n"
        "📅 **Год** — 12 390 ₽ (экономия 3 090 ₽)\n"
        "Максимальная выгода для полной трансформации\n\n"
        "✅ Все планы включают:\n"
        "• Персональное меню на каждый день\n"
        "• Программу тренировок\n"
        "• Ежедневную поддержку\n"
        "• Адаптацию под твой прогресс"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_subscription_keyboard(),
        parse_mode="Markdown"
    )