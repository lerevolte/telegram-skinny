from typing import Dict, Any, List
import openai
from datetime import datetime, timedelta

class NutritionService:
    """Сервис для работы с питанием"""
    
    def calculate_nutrition(
        self,
        gender: str,
        age: int,
        height: float,
        weight: float,
        activity_level: str,
        goal: str,
        target_weight: float = None
    ) -> Dict[str, int]:
        """Расчет КБЖУ"""
        
        # Расчет базового метаболизма (формула Миффлина-Сан Жеора)
        if gender == "male":
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161
        
        # Коэффициенты активности
        activity_multipliers = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very_active": 1.9
        }
        
        tdee = bmr * activity_multipliers[activity_level]
        
        # Корректировка под цель
        if goal == "weight_loss":
            calories = int(tdee * 0.8)  # Дефицит 20%
            protein_ratio = 0.3
            carbs_ratio = 0.35
            fats_ratio = 0.35
        elif goal == "muscle_gain":
            calories = int(tdee * 1.1)  # Профицит 10%
            protein_ratio = 0.3
            carbs_ratio = 0.45
            fats_ratio = 0.25
        elif goal == "tone":
            calories = int(tdee * 0.9)  # Небольшой дефицит
            protein_ratio = 0.35
            carbs_ratio = 0.35
            fats_ratio = 0.3
        else:  # maintain
            calories = int(tdee)
            protein_ratio = 0.25
            carbs_ratio = 0.45
            fats_ratio = 0.3
        
        # Расчет БЖУ
        protein = int((calories * protein_ratio) / 4)  # 4 ккал/г
        carbs = int((calories * carbs_ratio) / 4)
        fats = int((calories * fats_ratio) / 9)  # 9 ккал/г
        
        return {
            "bmr": bmr,
            "tdee": tdee,
            "calories": calories,
            "protein": protein,
            "carbs": carbs,
            "fats": fats
        }
    
    async def generate_meal_plan(
        self,
        user_data: Dict[str, Any],
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Генерация плана питания через AI"""
        
        prompt = f"""
        Создай план питания на {days} дней для человека со следующими параметрами:
        - Калории в день: {user_data['daily_calories']} ккал
        - Белки: {user_data['daily_protein']}г
        - Углеводы: {user_data['daily_carbs']}г
        - Жиры: {user_data['daily_fats']}г
        - Приемов пищи: {user_data['meals_per_day']}
        - Ограничения: {', '.join(user_data.get('dietary_restrictions', []))}
        - Бюджет: {user_data.get('budget', 'средний')}
        
        Для каждого дня предложи конкретные блюда с указанием:
        - Название блюда
        - Ингредиенты с граммовками
        - КБЖУ
        - Простой рецепт приготовления
        
        Ответ в формате JSON.
        """
        
        # Здесь вызов OpenAI API или другой LLM
        # Для примера возвращаем заглушку
        return self._generate_sample_meal_plan(user_data, days)
    
    def _generate_sample_meal_plan(self, user_data: Dict, days: int) -> List[Dict]:
        """Пример генерации плана питания"""
        meal_plan = []
        
        for day in range(1, days + 1):
            daily_plan = {
                "day": day,
                "meals": [],
                "total_calories": user_data['daily_calories'],
                "total_protein": user_data['daily_protein'],
                "total_carbs": user_data['daily_carbs'],
                "total_fats": user_data['daily_fats']
            }
            
            # Распределение калорий по приемам пищи
            if user_data['meals_per_day'] == 3:
                meal_distribution = [0.3, 0.4, 0.3]  # Завтрак, обед, ужин
                meal_names = ["breakfast", "lunch", "dinner"]
            else:
                meal_distribution = [0.25, 0.35, 0.25, 0.15]  # + перекус
                meal_names = ["breakfast", "lunch", "dinner", "snack"]
            
            for i, (meal_name, distribution) in enumerate(zip(meal_names, meal_distribution)):
                meal_calories = int(user_data['daily_calories'] * distribution)
                meal_protein = int(user_data['daily_protein'] * distribution)
                meal_carbs = int(user_data['daily_carbs'] * distribution)
                meal_fats = int(user_data['daily_fats'] * distribution)
                
                meal = {
                    "type": meal_name,
                    "name": self._get_meal_name(meal_name, day),
                    "calories": meal_calories,
                    "protein": meal_protein,
                    "carbs": meal_carbs,
                    "fats": meal_fats,
                    "ingredients": self._get_meal_ingredients(meal_name),
                    "recipe": "Простой рецепт приготовления..."
                }
                
                daily_plan["meals"].append(meal)
            
            meal_plan.append(daily_plan)
        
        return meal_plan
    
    def _get_meal_name(self, meal_type: str, day: int) -> str:
        """Получение названия блюда"""
        meals = {
            "breakfast": [
                "Овсянка с ягодами и орехами",
                "Яичница с овощами",
                "Творожная запеканка",
                "Гречневая каша с молоком",
                "Омлет с сыром",
                "Сырники со сметаной",
                "Мюсли с йогуртом"
            ],
            "lunch": [
                "Куриная грудка с рисом",
                "Паста с томатным соусом",
                "Рыба с овощами на пару",
                "Говядина с гречкой",
                "Суп-пюре из брокколи",
                "Плов с курицей",
                "Лосось с киноа"
            ],
            "dinner": [
                "Салат Цезарь с курицей",
                "Овощное рагу",
                "Творог с фруктами",
                "Греческий салат",
                "Запеченные овощи",
                "Рыбные котлеты",
                "Куриное филе с салатом"
            ],
            "snack": [
                "Протеиновый батончик",
                "Яблоко с арахисовой пастой",
                "Греческий йогурт",
                "Орехи и сухофрукты",
                "Творожок",
                "Банан",
                "Протеиновый коктейль"
            ]
        }
        
        return meals[meal_type][(day - 1) % len(meals[meal_type])]
    
    def _get_meal_ingredients(self, meal_type: str) -> List[Dict]:
        """Получение ингредиентов блюда"""
        # Упрощенный пример
        return [
            {"name": "Основной продукт", "amount": "150г"},
            {"name": "Гарнир", "amount": "100г"},
            {"name": "Овощи", "amount": "200г"}
        ]