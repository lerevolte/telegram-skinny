from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from typing import Dict, Any

from states.user_states import OnboardingStates
from keyboards.inline import (
    get_gender_keyboard,
    get_activity_keyboard,
    get_goal_keyboard,
    get_meal_count_keyboard,
    get_restrictions_keyboard
)
from core.services.user_service import UserService
from core.services.nutrition_service import NutritionService
from utils.validators import validate_age, validate_height, validate_weight

router = Router()
user_service = UserService()
nutrition_service = NutritionService()

@router.callback_query(OnboardingStates.gender)
async def process_gender(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора пола"""
    await state.update_data(gender=callback.data)
    await callback.message.edit_text("Отлично! Теперь укажи свой возраст:")
    await state.set_state(OnboardingStates.age)

@router.message(OnboardingStates.age)
async def process_age(message: Message, state: FSMContext):
    """Обработка возраста"""
    if not validate_age(message.text):
        await message.answer("Пожалуйста, укажи корректный возраст (от 14 до 100 лет)")
        return
    
    await state.update_data(age=int(message.text))
    await message.answer("Укажи свой рост в сантиметрах:")
    await state.set_state(OnboardingStates.height)

@router.message(OnboardingStates.height)
async def process_height(message: Message, state: FSMContext):
    """Обработка роста"""
    if not validate_height(message.text):
        await message.answer("Пожалуйста, укажи корректный рост (от 120 до 250 см)")
        return
    
    await state.update_data(height=float(message.text))
    await message.answer("Укажи свой текущий вес в килограммах:")
    await state.set_state(OnboardingStates.weight)

@router.message(OnboardingStates.weight)
async def process_weight(message: Message, state: FSMContext):
    """Обработка веса"""
    if not validate_weight(message.text):
        await message.answer("Пожалуйста, укажи корректный вес (от 30 до 300 кг)")
        return
    
    await state.update_data(weight=float(message.text))
    await message.answer("Какая у тебя цель?", reply_markup=get_goal_keyboard())
    await state.set_state(OnboardingStates.goal)

@router.callback_query(OnboardingStates.goal)
async def process_goal(callback: CallbackQuery, state: FSMContext):
    """Обработка цели"""
    await state.update_data(goal=callback.data)
    
    if callback.data in ["weight_loss", "tone"]:
        await callback.message.edit_text("Какой вес ты хочешь достичь?")
        await state.set_state(OnboardingStates.target_weight)
    else:
        await callback.message.edit_text(
            "Какой у тебя уровень активности?",
            reply_markup=get_activity_keyboard()
        )
        await state.set_state(OnboardingStates.activity_level)

@router.message(OnboardingStates.target_weight)
async def process_target_weight(message: Message, state: FSMContext):
    """Обработка целевого веса"""
    if not validate_weight(message.text):
        await message.answer("Пожалуйста, укажи корректный целевой вес")
        return
    
    await state.update_data(target_weight=float(message.text))
    await message.answer(
        "Какой у тебя уровень активности?",
        reply_markup=get_activity_keyboard()
    )
    await state.set_state(OnboardingStates.activity_level)

@router.callback_query(OnboardingStates.activity_level)
async def process_activity(callback: CallbackQuery, state: FSMContext):
    """Обработка уровня активности"""
    await state.update_data(activity_level=callback.data)
    await callback.message.edit_text(
        "Сколько раз в день ты предпочитаешь есть?",
        reply_markup=get_meal_count_keyboard()
    )
    await state.set_state(OnboardingStates.meals_per_day)

@router.callback_query(OnboardingStates.meals_per_day)
async def process_meals(callback: CallbackQuery, state: FSMContext):
    """Обработка количества приемов пищи"""
    await state.update_data(meals_per_day=int(callback.data))
    await callback.message.edit_text(
        "Есть ли у тебя ограничения в питании?",
        reply_markup=get_restrictions_keyboard()
    )
    await state.set_state(OnboardingStates.restrictions)

@router.callback_query(OnboardingStates.restrictions)
async def process_restrictions(callback: CallbackQuery, state: FSMContext):
    """Обработка ограничений в питании"""
    data = await state.get_data()
    restrictions = data.get("dietary_restrictions", [])
    
    if callback.data == "done_restrictions":
        await finalize_onboarding(callback.message, state)
    else:
        if callback.data in restrictions:
            restrictions.remove(callback.data)
        else:
            restrictions.append(callback.data)
        
        await state.update_data(dietary_restrictions=restrictions)
        await callback.message.edit_reply_markup(
            reply_markup=get_restrictions_keyboard(selected=restrictions)
        )

async def finalize_onboarding(message: Message, state: FSMContext):
    """Завершение онбординга и создание плана"""
    data = await state.get_data()
    
    # Сохранение данных пользователя
    user = await user_service.update_user_profile(
        telegram_id=message.chat.id,
        **data
    )
    
    # Расчет калорий и БЖУ
    nutrition_data = nutrition_service.calculate_nutrition(
        gender=data["gender"],
        age=data["age"],
        height=data["height"],
        weight=data["weight"],
        activity_level=data["activity_level"],
        goal=data["goal"],
        target_weight=data.get("target_weight")
    )
    
    await user_service.update_nutrition_targets(user.id, nutrition_data)
    
    # Генерация плана питания
    await message.answer(
        "🎉 Отлично! Твой персональный план готов!\n\n"
        f"📊 Твои параметры:\n"
        f"• Калории: {nutrition_data['calories']} ккал/день\n"
        f"• Белки: {nutrition_data['protein']}г\n"
        f"• Углеводы: {nutrition_data['carbs']}г\n"
        f"• Жиры: {nutrition_data['fats']}г\n\n"
        "Сейчас я создам для тебя меню на неделю..."
    )
    
    # Запуск генерации меню в фоне
    from workers.tasks import generate_meal_plan_task
    generate_meal_plan_task.delay(user.id)
    
    await state.clear()