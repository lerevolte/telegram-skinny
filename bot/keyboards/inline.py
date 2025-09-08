from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional

def get_start_keyboard(has_subscription: bool = False) -> InlineKeyboardMarkup:
    """Стартовая клавиатура"""
    builder = InlineKeyboardBuilder()
    
    if has_subscription:
        builder.button(text="📊 Мой план", callback_data="my_plan")
        builder.button(text="✅ Чек-ин", callback_data="daily_checkin")
        builder.button(text="📈 Прогресс", callback_data="progress")
        builder.button(text="⚙️ Настройки", callback_data="settings")
    else:
        builder.button(text="🚀 Начать бесплатный период (7 дней)", callback_data="start_trial")
        builder.button(text="💎 Купить подписку", callback_data="buy_subscription")
    
    builder.button(text="ℹ️ О боте", callback_data="about")
    builder.adjust(1)
    
    return builder.as_markup()

def get_subscription_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора подписки"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📅 Месяц — 1 290 ₽", callback_data="pay_monthly")
    builder.button(text="📅 3 месяца — 3 490 ₽ (-20%)", callback_data="pay_quarterly")
    builder.button(text="📅 Год — 12 390 ₽ (-20%)", callback_data="pay_yearly")
    builder.button(text="🔙 Назад", callback_data="back_to_start")
    
    builder.adjust(1)
    return builder.as_markup()

def get_gender_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора пола"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="👨 Мужской", callback_data="male")
    builder.button(text="👩 Женский", callback_data="female")
    
    builder.adjust(2)
    return builder.as_markup()

def get_activity_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура уровня активности"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🪑 Сидячий образ жизни", callback_data="sedentary")
    builder.button(text="🚶 Легкая активность (1-3 дня/нед)", callback_data="light")
    builder.button(text="🏃 Умеренная активность (3-5 дней/нед)", callback_data="moderate")
    builder.button(text="💪 Высокая активность (6-7 дней/нед)", callback_data="active")
    builder.button(text="🔥 Очень высокая активность", callback_data="very_active")
    
    builder.adjust(1)
    return builder.as_markup()

def get_goal_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора цели"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="⬇️ Похудеть", callback_data="weight_loss")
    builder.button(text="💪 Набрать мышечную массу", callback_data="muscle_gain")
    builder.button(text="🎯 Поддерживать форму", callback_data="maintain")
    builder.button(text="✨ Подтянуть тело", callback_data="tone")
    
    builder.adjust(1)
    return builder.as_markup()

def get_meal_count_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура количества приемов пищи"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="3 раза в день", callback_data="3")
    builder.button(text="4 раза в день", callback_data="4")
    builder.button(text="5 раз в день", callback_data="5")
    
    builder.adjust(1)
    return builder.as_markup()

def get_restrictions_keyboard(selected: List[str] = None) -> InlineKeyboardMarkup:
    """Клавиатура ограничений в питании"""
    if selected is None:
        selected = []
    
    builder = InlineKeyboardBuilder()
    
    restrictions = [
        ("🥬 Вегетарианство", "vegetarian"),
        ("🌱 Веганство", "vegan"),
        ("🥛 Без лактозы", "lactose_free"),
        ("🌾 Без глютена", "gluten_free"),
        ("🥜 Аллергия на орехи", "nuts_allergy"),
        ("🦐 Аллергия на морепродукты", "seafood_allergy"),
        ("🍳 Аллергия на яйца", "eggs_allergy"),
        ("🍖 Не ем красное мясо", "no_red_meat"),
        ("🐟 Не ем рыбу", "no_fish"),
    ]
    
    for text, data in restrictions:
        if data in selected:
            builder.button(text=f"✅ {text}", callback_data=data)
        else:
            builder.button(text=text, callback_data=data)
    
    builder.button(text="✅ Готово", callback_data="done_restrictions")
    
    builder.adjust(1)
    return builder.as_markup()

def get_morning_checkin_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура утреннего чек-ина"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="⚖️ Ввести вес", callback_data="enter_weight")
    builder.button(text="⏭️ Пропустить", callback_data="skip_weight")
    
    builder.adjust(2)
    return builder.as_markup()

def get_mood_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура настроения"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="😄 Отлично", callback_data="mood_great")
    builder.button(text="😊 Хорошо", callback_data="mood_good")
    builder.button(text="😐 Нормально", callback_data="mood_normal")
    builder.button(text="😔 Плохо", callback_data="mood_bad")
    
    builder.adjust(2)
    return builder.as_markup()

def get_workout_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения тренировки"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✅ Выполнил", callback_data="workout_done")
    builder.button(text="⏰ Сделаю позже", callback_data="workout_later")
    builder.button(text="❌ Пропускаю сегодня", callback_data="workout_skip")
    
    builder.adjust(1)
    return builder.as_markup()

def get_meal_plan_keyboard(day: int = 1) -> InlineKeyboardMarkup:
    """Клавиатура плана питания"""
    builder = InlineKeyboardBuilder()
    
    # Навигация по дням
    if day > 1:
        builder.button(text="◀️", callback_data=f"meal_day_{day-1}")
    
    builder.button(text=f"День {day}", callback_data="current_day")
    
    if day < 7:
        builder.button(text="▶️", callback_data=f"meal_day_{day+1}")
    
    # Действия с блюдами
    builder.button(text="🔄 Заменить блюдо", callback_data=f"replace_meal_{day}")
    builder.button(text="📋 Список покупок", callback_data="shopping_list")
    builder.button(text="📊 БЖУ дня", callback_data=f"day_macros_{day}")
    builder.button(text="🔙 Главное меню", callback_data="main_menu")
    
    builder.adjust(3, 1, 1, 1, 1)
    return builder.as_markup()

def get_replace_meal_keyboard(day: int, meal_type: str) -> InlineKeyboardMarkup:
    """Клавиатура замены блюда"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🥗 Проще приготовить", callback_data=f"replace_simple_{day}_{meal_type}")
    builder.button(text="💰 Дешевле", callback_data=f"replace_cheap_{day}_{meal_type}")
    builder.button(text="🥩 Больше белка", callback_data=f"replace_protein_{day}_{meal_type}")
    builder.button(text="🥦 Низкоуглеводное", callback_data=f"replace_lowcarb_{day}_{meal_type}")
    builder.button(text="🔙 Назад", callback_data=f"meal_day_{day}")
    
    builder.adjust(2, 2, 1)
    return builder.as_markup()

def get_workout_keyboard(week: int = 1, day: int = 1) -> InlineKeyboardMarkup:
    """Клавиатура тренировок"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="▶️ Начать тренировку", callback_data=f"start_workout_{week}_{day}")
    builder.button(text="📹 Видео упражнений", callback_data=f"workout_videos_{week}_{day}")
    builder.button(text="🔄 Заменить тренировку", callback_data=f"replace_workout_{week}_{day}")
    builder.button(text="📊 История тренировок", callback_data="workout_history")
    builder.button(text="🔙 Главное меню", callback_data="main_menu")
    
    builder.adjust(1)
    return builder.as_markup()

def get_payment_keyboard(amount: int, subscription_type: str) -> InlineKeyboardMarkup:
    """Клавиатура оплаты"""
    builder = InlineKeyboardBuilder()
    
    # Создаем инвойс для Telegram Payments
    builder.button(
        text=f"💳 Оплатить {amount // 100} ₽",
        pay=True  # Специальная кнопка для оплаты
    )
    builder.button(text="🔙 Назад", callback_data="buy_subscription")
    
    builder.adjust(1)
    return builder.as_markup()