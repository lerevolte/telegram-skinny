from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from typing import Dict, Any

from states.user_states import MealPlanStates
from keyboards.inline import (
    get_meal_plan_keyboard,
    get_replace_meal_keyboard,
    get_meal_type_keyboard
)
from core.services.user_service import UserService
from core.services.nutrition_service import NutritionService
from utils.ai_helpers import generate_meal_replacement

router = Router()
user_service = UserService()
nutrition_service = NutritionService()

@router.message(F.text == "📊 Мой план")
async def show_meal_plan(message: Message, state: FSMContext):
    """Показать план питания"""
    user = await user_service.get_user(telegram_id=message.from_user.id)
    
    if not user:
        await message.answer("Сначала пройди регистрацию /start")
        return
    
    # Получаем план на текущую неделю
    meal_plans = await user_service.get_meal_plans(user.id, week=1)
    
    if not meal_plans:
        await message.answer(
            "У тебя еще нет плана питания. Подожди, я его генерирую..."
        )
        # Запускаем генерацию
        from workers.tasks import generate_meal_plan_task
        generate_meal_plan_task.delay(user.id)
        return
    
    # Показываем план на первый день
    await show_day_plan(message, meal_plans[0], day=1)
    await state.set_state(MealPlanStates.viewing_day)
    await state.update_data(current_day=1, meal_plans=meal_plans)

async def show_day_plan(message: Message, meal_plan: Any, day: int):
    """Показать план на конкретный день"""
    text = f"📅 **День {day}**\n\n"
    
    # Завтрак
    if meal_plan.breakfast:
        text += f"🌅 **Завтрак** ({meal_plan.breakfast['calories']} ккал)\n"
        text += f"{meal_plan.breakfast['name']}\n"
        text += f"Б: {meal_plan.breakfast['protein']}г | "
        text += f"У: {meal_plan.breakfast['carbs']}г | "
        text += f"Ж: {meal_plan.breakfast['fats']}г\n\n"
    
    # Обед
    if meal_plan.lunch:
        text += f"☀️ **Обед** ({meal_plan.lunch['calories']} ккал)\n"
        text += f"{meal_plan.lunch['name']}\n"
        text += f"Б: {meal_plan.lunch['protein']}г | "
        text += f"У: {meal_plan.lunch['carbs']}г | "
        text += f"Ж: {meal_plan.lunch['fats']}г\n\n"
    
    # Ужин
    if meal_plan.dinner:
        text += f"🌙 **Ужин** ({meal_plan.dinner['calories']} ккал)\n"
        text += f"{meal_plan.dinner['name']}\n"
        text += f"Б: {meal_plan.dinner['protein']}г | "
        text += f"У: {meal_plan.dinner['carbs']}г | "
        text += f"Ж: {meal_plan.dinner['fats']}г\n\n"
    
    # Перекус
    if meal_plan.snack:
        text += f"🍎 **Перекус** ({meal_plan.snack['calories']} ккал)\n"
        text += f"{meal_plan.snack['name']}\n\n"
    
    # Итого
    text += f"📊 **Итого за день:**\n"
    text += f"Калории: {meal_plan.total_calories} ккал\n"
    text += f"Белки: {meal_plan.total_protein}г\n"
    text += f"Углеводы: {meal_plan.total_carbs}г\n"
    text += f"Жиры: {meal_plan.total_fats}г"
    
    await message.answer(
        text,
        reply_markup=get_meal_plan_keyboard(day),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("meal_day_"))
async def switch_day(callback: CallbackQuery, state: FSMContext):
    """Переключение между днями"""
    day = int(callback.data.split("_")[2])
    data = await state.get_data()
    meal_plans = data.get("meal_plans", [])
    
    if 0 < day <= len(meal_plans):
        await show_day_plan(callback.message, meal_plans[day-1], day)
        await state.update_data(current_day=day)
        await callback.answer()
    else:
        await callback.answer("План на этот день еще не готов", show_alert=True)

@router.callback_query(F.data.startswith("replace_meal_"))
async def start_meal_replacement(callback: CallbackQuery, state: FSMContext):
    """Начать замену блюда"""
    day = int(callback.data.split("_")[2])
    
    await callback.message.edit_text(
        "Какое блюдо хочешь заменить?",
        reply_markup=get_meal_type_keyboard(day)
    )
    await state.set_state(MealPlanStates.replacing_meal)

@router.callback_query(F.data.startswith("replace_") and MealPlanStates.replacing_meal)
async def process_replacement(callback: CallbackQuery, state: FSMContext):
    """Обработка замены блюда"""
    parts = callback.data.split("_")
    replacement_type = parts[1]  # simple, cheap, protein, lowcarb
    day = int(parts[2])
    meal_type = parts[3]  # breakfast, lunch, dinner, snack
    
    data = await state.get_data()
    meal_plans = data.get("meal_plans", [])
    
    if day <= len(meal_plans):
        meal_plan = meal_plans[day-1]
        current_meal = getattr(meal_plan, meal_type)
        
        if current_meal:
            await callback.message.edit_text("Генерирую замену... ⏳")
            
            # Генерация замены через AI
            replacement = await generate_meal_replacement(
                current_meal,
                replacement_type
            )
            
            # Обновляем план в БД
            await nutrition_service.update_meal(
                meal_plan.id,
                meal_type,
                replacement
            )
            
            # Показываем новое блюдо
            text = f"✅ Замена готова!\n\n"
            text += f"**{replacement['name']}**\n"
            text += f"Калории: {replacement['calories']} ккал\n"
            text += f"Б: {replacement['protein']}г | "
            text += f"У: {replacement['carbs']}г | "
            text += f"Ж: {replacement['fats']}г\n\n"
            
            if replacement.get('ingredients'):
                text += "📝 Ингредиенты:\n"
                for ing in replacement['ingredients']:
                    text += f"• {ing}\n"
                text += "\n"
            
            if replacement.get('recipe'):
                text += f"👨‍🍳 Рецепт:\n{replacement['recipe']}"
            
            await callback.message.edit_text(
                text,
                reply_markup=get_meal_plan_keyboard(day),
                parse_mode="Markdown"
            )
    
    await state.set_state(MealPlanStates.viewing_day)
    await callback.answer()

@router.callback_query(F.data == "shopping_list")
async def show_shopping_list(callback: CallbackQuery, state: FSMContext):
    """Показать список покупок"""
    data = await state.get_data()
    meal_plans = data.get("meal_plans", [])
    
    if not meal_plans:
        await callback.answer("План питания не загружен", show_alert=True)
        return
    
    # Собираем список покупок
    shopping_list = {}
    
    for plan in meal_plans:
        if plan.shopping_list:
            for item in plan.shopping_list:
                name = item['name']
                amount = item['amount']
                
                if name in shopping_list:
                    # Суммируем количество
                    shopping_list[name] += f", {amount}"
                else:
                    shopping_list[name] = amount
    
    # Формируем текст
    text = "🛒 **Список покупок на неделю:**\n\n"
    
    categories = {
        "Мясо/Рыба": ["курица", "говядина", "рыба", "индейка", "свинина"],
        "Молочные": ["молоко", "творог", "сыр", "йогурт", "кефир"],
        "Овощи": ["помидор", "огурец", "капуста", "морковь", "лук"],
        "Фрукты": ["яблоко", "банан", "апельсин", "груша", "ягоды"],
        "Крупы": ["рис", "гречка", "овсянка", "макароны", "хлеб"],
        "Другое": []
    }
    
    categorized = {cat: [] for cat in categories}
    
    for item, amount in shopping_list.items():
        added = False
        for category, keywords in categories.items():
            if any(keyword in item.lower() for keyword in keywords):
                categorized[category].append(f"• {item}: {amount}")
                added = True
                break
        if not added:
            categorized["Другое"].append(f"• {item}: {amount}")
    
    for category, items in categorized.items():
        if items:
            text += f"**{category}:**\n"
            text += "\n".join(items) + "\n\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_meal_plan_keyboard(data.get("current_day", 1)),
        parse_mode="Markdown"
    )
    await callback.answer()