from typing import Optional
import re

def validate_age(age_text: str) -> bool:
    """Валидация возраста"""
    try:
        age = int(age_text)
        return 14 <= age <= 100
    except ValueError:
        return False

def validate_height(height_text: str) -> bool:
    """Валидация роста в см"""
    try:
        height = float(height_text.replace(',', '.'))
        return 120 <= height <= 250
    except ValueError:
        return False

def validate_weight(weight_text: str) -> bool:
    """Валидация веса в кг"""
    try:
        weight = float(weight_text.replace(',', '.'))
        return 30 <= weight <= 300
    except ValueError:
        return False

def validate_water(water_text: str) -> bool:
    """Валидация количества воды в мл"""
    try:
        water = int(water_text)
        return 0 <= water <= 10000
    except ValueError:
        return False

def validate_steps(steps_text: str) -> bool:
    """Валидация количества шагов"""
    try:
        steps = int(steps_text)
        return 0 <= steps <= 100000
    except ValueError:
        return False

def validate_sleep(sleep_text: str) -> bool:
    """Валидация часов сна"""
    try:
        sleep = float(sleep_text.replace(',', '.'))
        return 0 <= sleep <= 24
    except ValueError:
        return False

def validate_phone(phone: str) -> bool:
    """Валидация номера телефона"""
    pattern = r'^[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,3}[)]?[-\s\.]?[0-9]{3,5}[-\s\.]?[0-9]{3,5}$'
    return bool(re.match(pattern, phone))

def validate_email(email: str) -> bool:
    """Валидация email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def sanitize_input(text: str, max_length: int = 500) -> str:
    """Очистка пользовательского ввода"""
    # Удаляем лишние пробелы
    text = ' '.join(text.split())
    # Обрезаем до максимальной длины
    text = text[:max_length]
    # Экранируем HTML
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    return text

def calculate_bmi(weight: float, height: float) -> tuple[float, str]:
    """Расчет индекса массы тела"""
    height_m = height / 100
    bmi = weight / (height_m ** 2)
    
    if bmi < 18.5:
        category = "Недостаточный вес"
    elif 18.5 <= bmi < 25:
        category = "Нормальный вес"
    elif 25 <= bmi < 30:
        category = "Избыточный вес"
    else:
        category = "Ожирение"
    
    return round(bmi, 1), category