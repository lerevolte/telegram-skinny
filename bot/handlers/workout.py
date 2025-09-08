from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
import asyncio

from states.user_states import WorkoutStates
from keyboards.inline import get_workout_keyboard
from core.services.workout_service import WorkoutService
from utils.ai_helpers import generate_workout_advice

router = Router()
workout_service = WorkoutService()

@router.message(F.text == "🏋️ Тренировка")
async def show_workout(message: Message, state: FSMContext):
    """Показать тренировку на сегодня"""
    user = await workout_service.get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        await message.answer("Сначала пройди регистрацию /start")
        return
    
    # Получаем тренировку на сегодня
    today_workout = await workout_service.get_today_workout(user.id)
    
    if not today_workout:
        await message.answer(
            "На сегодня тренировка не запланирована. Отдыхай! 😊\n\n"
            "Следующая тренировка будет завтра."
        )
        return
    
    # Формируем описание тренировки
    text = await format_workout_text(today_workout)
    
    await message.answer(
        text,
        reply_markup=get_workout_keyboard(
            week=today_workout.week_number,
            day=today_workout.day_number
        ),
        parse_mode="Markdown"
    )
    
    await state.set_state(WorkoutStates.selecting_workout)
    await state.update_data(workout_id=today_workout.id)

async def format_workout_text(workout) -> str:
    """Форматирование текста тренировки"""
    text = f"💪 **Тренировка на сегодня**\n\n"
    text += f"Тип: {workout.workout_type}\n"
    text += f"Длительность: {workout.duration_minutes} минут\n"
    text += f"Уровень: {workout.difficulty}\n"
    text += f"Калории: ~{workout.calories_burned} ккал\n\n"
    
    text += "📋 **Упражнения:**\n\n"
    
    for i, exercise in enumerate(workout.exercises, 1):
        text += f"{i}. **{exercise['name']}**\n"
        
        if exercise.get('sets') and exercise.get('reps'):
            text += f"   {exercise['sets']} подхода × {exercise['reps']} раз\n"
        elif exercise.get('duration'):
            text += f"   {exercise['duration']} секунд\n"
        
        if exercise.get('rest'):
            text += f"   Отдых: {exercise['rest']} сек\n"
        
        text += "\n"
    
    return text

@router.callback_query(F.data.startswith("start_workout_"))
async def start_workout(callback: CallbackQuery, state: FSMContext):
    """Начать тренировку"""
    parts = callback.data.split("_")
    week = int(parts[2])
    day = int(parts[3])
    
    data = await state.get_data()
    workout_id = data.get("workout_id")
    
    await callback.message.edit_text(
        "🏃‍♂️ Отлично! Начинаем тренировку!\n\n"
        "Я буду показывать упражнения по одному.\n"
        "Готов? Поехали! 🚀"
    )
    
    await state.set_state(WorkoutStates.in_progress)
    
    # Получаем тренировку
    workout = await workout_service.get_workout_by_id(workout_id)
    
    # Проходим по упражнениям
    for i, exercise in enumerate(workout.exercises, 1):
        await show_exercise(callback.message, exercise, i, len(workout.exercises))
        
        # Даем время на выполнение
        if exercise.get('duration'):
            await asyncio.sleep(exercise['duration'])
        else:
            # Примерное время на подход
            sets = exercise.get('sets', 3)
            reps = exercise.get('reps', 12)
            rest = exercise.get('rest', 60)
            
            exercise_time = sets * (reps * 3 + rest)  # 3 сек на повторение
            await asyncio.sleep(min(exercise_time, 180))  # Максимум 3 минуты
    
    # Завершение тренировки
    await complete_workout(callback.message, state, workout_id)

async def show_exercise(message: Message, exercise: dict, current: int, total: int):
    """Показать упражнение"""
    text = f"**Упражнение {current}/{total}**\n\n"
    text += f"🎯 **{exercise['name']}**\n\n"
    
    if exercise.get('description'):
        text += f"{exercise['description']}\n\n"
    
    if exercise.get('sets') and exercise.get('reps'):
        text += f"📊 Выполни: {exercise['sets']} × {exercise['reps']}\n"
    elif exercise.get('duration'):
        text += f"⏱ Время: {exercise['duration']} секунд\n"
    
    if exercise.get('rest'):
        text += f"😴 Отдых после: {exercise['rest']} сек\n"
    
    if exercise.get('tips'):
        text += f"\n💡 Совет: {exercise['tips']}"
    
    await message.answer(text, parse_mode="Markdown")

async def complete_workout(message: Message, state: FSMContext, workout_id: int):
    """Завершение тренировки"""
    # Отмечаем тренировку как выполненную
    await workout_service.mark_workout_completed(workout_id)
    
    # Получаем данные пользователя для генерации совета
    user_data = await state.get_data()
    advice = await generate_workout_advice(user_data)
    
    await message.answer(
        "🎉 **Поздравляю! Тренировка завершена!**\n\n"
        f"{advice}\n\n"
        "Не забудь:\n"
        "• Выпить воды 💧\n"
        "• Сделать растяжку 🧘\n"
        "• Записать ощущения в дневник 📝\n\n"
        "Отличная работа! До встречи на следующей тренировке! 💪",
        parse_mode="Markdown"
    )
    
    await state.clear()

@router.callback_query(F.data.startswith("workout_videos_"))
async def show_workout_videos(callback: CallbackQuery):
    """Показать видео упражнений"""
    # Здесь можно добавить ссылки на YouTube или свои видео
    
    videos = {
        "Приседания": "https://youtube.com/watch?v=...",
        "Отжимания": "https://youtube.com/watch?v=...",
        "Планка": "https://youtube.com/watch?v=...",
        "Берпи": "https://youtube.com/watch?v=...",
        "Выпады": "https://youtube.com/watch?v=..."
    }
    
    text = "📹 **Видео-инструкции:**\n\n"
    for name, url in videos.items():
        text += f"• [{name}]({url})\n"
    
    text += "\n💡 Совет: Сначала посмотри технику, потом выполняй!"
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
    await callback.answer()

@router.callback_query(F.data.startswith("replace_workout_"))
async def replace_workout(callback: CallbackQuery):
    """Заменить тренировку"""
    await callback.message.edit_text(
        "Выбери альтернативную тренировку:\n\n"
        "🏃‍♂️ **Кардио** (30 мин)\n"
        "Бег, велосипед или быстрая ходьба\n\n"
        "🧘 **Йога** (20 мин)\n"
        "Растяжка и расслабление\n\n"
        "🏊‍♂️ **Плавание** (30 мин)\n"
        "Если есть доступ к бассейну\n\n"
        "🚶‍♂️ **Прогулка** (45 мин)\n"
        "Активная прогулка на свежем воздухе\n\n"
        "Выбери подходящий вариант и отметь выполнение!"
    )
    await callback.answer("Выбери активность и отметь в чек-ине", show_alert=True)

@router.callback_query(F.data == "workout_history")
async def show_workout_history(callback: CallbackQuery):
    """Показать историю тренировок"""
    user = await workout_service.get_user_by_telegram_id(callback.from_user.id)
    
    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return
    
    # Получаем последние 10 тренировок
    history = await workout_service.get_workout_history(user.id, limit=10)
    
    if not history:
        await callback.message.edit_text(
            "У тебя пока нет выполненных тренировок.\n"
            "Начни прямо сегодня! 💪"
        )
        return
    
    text = "📊 **История тренировок:**\n\n"
    
    for workout in history:
        date = workout.completed_at.strftime("%d.%m")
        emoji = "✅" if workout.completed else "⏭"
        text += f"{emoji} {date} - {workout.workout_type} ({workout.duration_minutes} мин)\n"
    
    # Статистика
    total_workouts = len([w for w in history if w.completed])
    total_calories = sum(w.calories_burned for w in history if w.completed)
    
    text += f"\n📈 **Статистика:**\n"
    text += f"• Выполнено тренировок: {total_workouts}\n"
    text += f"• Сожжено калорий: {total_calories} ккал\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.answer()