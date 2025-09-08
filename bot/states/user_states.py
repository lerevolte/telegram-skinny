from aiogram.fsm.state import State, StatesGroup

class OnboardingStates(StatesGroup):
    """Состояния онбординга"""
    gender = State()
    age = State()
    height = State()
    weight = State()
    target_weight = State()
    goal = State()
    activity_level = State()
    meals_per_day = State()
    restrictions = State()
    allergies = State()
    budget = State()
    cuisines = State()

class CheckInStates(StatesGroup):
    """Состояния чек-ина"""
    morning_weight = State()
    weight_input = State()
    mood = State()
    sleep_hours = State()
    day_activity = State()
    water_intake = State()
    steps_count = State()
    evening_food = State()
    daily_reflection = State()

class MealPlanStates(StatesGroup):
    """Состояния работы с планом питания"""
    viewing_day = State()
    replacing_meal = State()
    adding_note = State()

class WorkoutStates(StatesGroup):
    """Состояния тренировок"""
    selecting_workout = State()
    in_progress = State()
    completing = State()
    rating = State()

class PaymentStates(StatesGroup):
    """Состояния оплаты"""
    selecting_plan = State()
    entering_promo = State()
    processing = State()