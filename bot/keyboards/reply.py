from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню (reply keyboard)"""
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="📊 Мой план")
    builder.button(text="✅ Чек-ин")
    builder.button(text="🏋️ Тренировка")
    builder.button(text="📈 Прогресс")
    builder.button(text="💬 Поддержка")
    builder.button(text="⚙️ Настройки")
    
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True)

def get_quick_actions_keyboard() -> ReplyKeyboardMarkup:
    """Быстрые действия"""
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="📸 Отправить фото еды")
    builder.button(text="⚖️ Записать вес")
    builder.button(text="💧 Отметить воду")
    builder.button(text="👟 Записать шаги")
    
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True)

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура отмены"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Отмена")
    return builder.as_markup(resize_keyboard=True)