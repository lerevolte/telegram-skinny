from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, PhotoSize
from aiogram.fsm.context import FSMContext
from datetime import datetime, time
import asyncio

from states.user_states import CheckInStates
from keyboards.inline import (
    get_morning_checkin_keyboard,
    get_mood_keyboard,
    get_workout_confirmation_keyboard
)
from core.services.checkin_service import CheckInService
from core.services.storage_service import StorageService
from utils.ai_helpers import analyze_food_photo

router = Router()
checkin_service = CheckInService()
storage_service = StorageService()

@router.message(F.text == "/checkin")
async def start_checkin(message: Message, state: FSMContext):
    """Начало ежедневного чек-ина"""
    current_hour = datetime.now().hour
    
    if 5 <= current_hour < 12:
        # Утренний чек-ин
        await message.answer(
            "Доброе утро! ☀️\n"
            "Давай начнем день с проверки твоего состояния.",
            reply_markup=get_morning_checkin_keyboard()
        )
        await state.set_state(CheckInStates.morning_weight)
    elif 12 <= current_hour < 18:
        # Дневной чек-ин
        await message.answer(
            "Привет! Как проходит твой день?\n"
            "Не забудь про воду и движение! 💧",
            reply_markup=get_workout_confirmation_keyboard()
        )
        await state.set_state(CheckInStates.day_activity)
    else:
        # Вечерний чек-ин
        await message.answer(
            "Добрый вечер! 🌙\n"
            "Давай подведем итоги дня.\n"
            "Отправь фото своего ужина или напиши, что ел сегодня."
        )
        await state.set_state(CheckInStates.evening_food)

@router.callback_query(CheckInStates.morning_weight, F.data == "enter_weight")
async def request_weight(callback: CallbackQuery, state: FSMContext):
    """Запрос веса"""
    await callback.message.edit_text("Введи свой текущий вес (в кг):")
    await state.set_state(CheckInStates.weight_input)

@router.message(CheckInStates.weight_input)
async def process_weight(message: Message, state: FSMContext):
    """Обработка введенного веса"""
    try:
        weight = float(message.text.replace(',', '.'))
        if not 30 <= weight <= 300:
            raise ValueError
        
        await state.update_data(morning_weight=weight)
        await checkin_service.log_weight(message.from_user.id, weight)
        
        await message.answer(
            f"✅ Вес записан: {weight} кг\n\n"
            "Как ты себя чувствуешь?",
            reply_markup=get_mood_keyboard()
        )
        await state.set_state(CheckInStates.mood)
    except ValueError:
        await message.answer("Пожалуйста, введи корректный вес (30-300 кг)")

@router.callback_query(CheckInStates.mood)
async def process_mood(callback: CallbackQuery, state: FSMContext):
    """Обработка настроения"""
    mood = callback.data.replace("mood_", "")
    await state.update_data(mood=mood)
    
    mood_responses = {
        "great": "Отлично! Используй эту энергию по максимуму! 💪",
        "good": "Хорошее начало дня! Продолжай в том же духе! 👍",
        "normal": "Стабильность - ключ к успеху! Двигаемся дальше! 🎯",
        "bad": "Бывает! Главное - не сдаваться. Я помогу тебе! 💚"
    }
    
    await callback.message.edit_text(
        mood_responses[mood] + "\n\nСколько часов ты спал?"
    )
    await state.set_state(CheckInStates.sleep_hours)

@router.message(CheckInStates.sleep_hours)
async def process_sleep(message: Message, state: FSMContext):
    """Обработка часов сна"""
    try:
        sleep = float(message.text.replace(',', '.'))
        if not 0 <= sleep <= 24:
            raise ValueError
        
        await state.update_data(sleep_hours=sleep)
        
        # Сохранение утреннего чек-ина
        data = await state.get_data()
        await checkin_service.save_morning_checkin(
            user_id=message.from_user.id,
            **data
        )
        
        sleep_advice = ""
        if sleep < 6:
            sleep_advice = "⚠️ Мало сна может замедлить прогресс. Постарайся спать 7-9 часов."
        elif sleep > 9:
            sleep_advice = "😴 Много сна тоже может влиять на метаболизм."
        else:
            sleep_advice = "✅ Отличное количество сна для восстановления!"
        
        await message.answer(
            f"{sleep_advice}\n\n"
            "Твой план на сегодня готов! Проверь его в главном меню.\n"
            "Не забудь отметить тренировку и отправить фото еды! 📸"
        )
        await state.clear()
        
    except ValueError:
        await message.answer("Пожалуйста, введи количество часов (0-24)")

@router.message(CheckInStates.evening_food, F.photo)
async def process_food_photo(message: Message, state: FSMContext):
    """Обработка фото еды"""
    photo: PhotoSize = message.photo[-1]  # Берем самое большое фото
    
    # Сохранение фото в S3
    file_info = await message.bot.get_file(photo.file_id)
    photo_url = await storage_service.save_photo(
        file_info,
        f"food/{message.from_user.id}/{datetime.now().isoformat()}.jpg"
    )
    
    # Анализ фото с помощью AI
    await message.answer("Анализирую фото... 🔍")
    food_analysis = await analyze_food_photo(photo_url)
    
    await state.update_data(
        food_photo=photo_url,
        estimated_calories=food_analysis.get("calories", 0)
    )
    
    await message.answer(
        f"📊 Анализ блюда:\n"
        f"• Примерные калории: {food_analysis.get('calories', 'не определено')} ккал\n"
        f"• Белки: {food_analysis.get('protein', '?')}г\n"
        f"• Углеводы: {food_analysis.get('carbs', '?')}г\n"
        f"• Жиры: {food_analysis.get('fats', '?')}г\n\n"
        f"💡 Совет: {food_analysis.get('advice', 'Продолжай следить за питанием!')}"
    )
    
    await checkin_service.save_food_log(
        user_id=message.from_user.id,
        meal_type="dinner",
        **await state.get_data()
    )
    
    await message.answer("Отличная работа сегодня! Увидимся завтра! 🌙")
    await state.clear()