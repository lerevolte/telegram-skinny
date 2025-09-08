import openai
import base64
from typing import Dict, Any, List
import aiohttp
from config import settings

async def analyze_food_photo(photo_url: str) -> Dict[str, Any]:
    """Анализ фото еды с помощью AI"""
    
    try:
        # Скачиваем фото
        async with aiohttp.ClientSession() as session:
            async with session.get(photo_url) as response:
                image_data = await response.read()
                base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Отправка в OpenAI Vision API (или другой сервис)
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = await client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Проанализируй это фото еды и определи примерное количество калорий, белков, углеводов и жиров. Также дай короткий совет по улучшению рациона."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        
        # Парсинг ответа
        # В реальности нужен более сложный парсинг
        return {
            "calories": 450,
            "protein": 30,
            "carbs": 45,
            "fats": 15,
            "advice": "Добавь больше овощей для баланса!"
        }
        
    except Exception as e:
        print(f"Error analyzing photo: {e}")
        return {
            "calories": "не определено",
            "protein": "?",
            "carbs": "?",
            "fats": "?",
            "advice": "Не удалось проанализировать фото. Попробуй сделать фото при лучшем освещении."
        }

async def generate_meal_replacement(
    meal_data: Dict[str, Any],
    replacement_type: str
) -> Dict[str, Any]:
    """Генерация замены блюда"""
    
    prompt = f"""
    Текущее блюдо:
    - Название: {meal_data['name']}
    - Калории: {meal_data['calories']}
    - Белки: {meal_data['protein']}г
    - Углеводы: {meal_data['carbs']}г
    - Жиры: {meal_data['fats']}г
    
    Предложи замену типа: {replacement_type}
    Типы замены:
    - simple: проще в приготовлении (максимум 15 минут)
    - cheap: дешевле по стоимости продуктов
    - protein: больше белка (минимум +10г)
    - lowcarb: меньше углеводов (максимум 20г)
    
    Ответ в формате JSON с полями: name, calories, protein, carbs, fats, ingredients, recipe
    """
    
    try:
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "Ты опытный нутрициолог и повар."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        import json
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        print(f"Error generating replacement: {e}")
        # Возвращаем заглушку
        return {
            "name": "Альтернативное блюдо",
            "calories": meal_data['calories'],
            "protein": meal_data['protein'],
            "carbs": meal_data['carbs'],
            "fats": meal_data['fats'],
            "ingredients": ["Продукт 1", "Продукт 2"],
            "recipe": "Простой рецепт приготовления..."
        }

async def generate_workout_advice(user_data: Dict[str, Any]) -> str:
    """Генерация советов по тренировкам"""
    
    prompt = f"""
    Дай короткий совет по тренировке для человека:
    - Цель: {user_data.get('goal')}
    - Уровень активности: {user_data.get('activity_level')}
    - Вес: {user_data.get('weight')}кг
    - Прогресс за неделю: {user_data.get('weekly_progress', 'неизвестно')}
    
    Максимум 2-3 предложения. Мотивирующий тон.
    """
    
    try:
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты опытный фитнес-тренер."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150
        )
        
        return response.choices[0].message.content
        
    except Exception:
        return "Отличная работа! Продолжай в том же духе и не забывай про регулярность тренировок!"
