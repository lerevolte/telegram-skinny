from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class UserStatus(enum.Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class ActivityLevel(enum.Enum):
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    VERY_ACTIVE = "very_active"

class Goal(enum.Enum):
    WEIGHT_LOSS = "weight_loss"
    MUSCLE_GAIN = "muscle_gain"
    MAINTAIN = "maintain"
    TONE = "tone"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255))
    last_name = Column(String(255), nullable=True)
    
    # Onboarding data
    gender = Column(String(10))
    age = Column(Integer)
    height = Column(Float)  # в см
    weight = Column(Float)  # в кг
    target_weight = Column(Float)
    goal = Column(Enum(Goal))
    activity_level = Column(Enum(ActivityLevel))
    
    # Preferences
    dietary_restrictions = Column(JSON, default=list)  # ["vegetarian", "no_gluten", etc.]
    allergies = Column(JSON, default=list)
    budget = Column(String(20))  # "low", "medium", "high"
    preferred_cuisines = Column(JSON, default=list)
    meals_per_day = Column(Integer, default=3)
    excluded_foods = Column(JSON, default=list)
    
    # Calculated data
    bmr = Column(Float)  # Базовый метаболизм
    tdee = Column(Float)  # Общий расход калорий
    daily_calories = Column(Integer)
    daily_protein = Column(Integer)
    daily_carbs = Column(Integer)
    daily_fats = Column(Integer)
    
    # Subscription
    status = Column(Enum(UserStatus), default=UserStatus.TRIAL)
    trial_start = Column(DateTime, nullable=True)
    subscription_start = Column(DateTime, nullable=True)
    subscription_end = Column(DateTime, nullable=True)
    subscription_type = Column(String(20))  # "monthly", "quarterly", "yearly"
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    meal_plans = relationship("MealPlan", back_populates="user")
    workouts = relationship("WorkoutPlan", back_populates="user")
    check_ins = relationship("DailyCheckIn", back_populates="user")
    weight_logs = relationship("WeightLog", back_populates="user")
    payments = relationship("Payment", back_populates="user")

class MealPlan(Base):
    __tablename__ = "meal_plans"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    week_number = Column(Integer)
    day_number = Column(Integer)  # 1-7
    
    breakfast = Column(JSON)  # {"name": "...", "calories": 300, "protein": 20, ...}
    lunch = Column(JSON)
    dinner = Column(JSON)
    snack = Column(JSON, nullable=True)
    
    total_calories = Column(Integer)
    total_protein = Column(Integer)
    total_carbs = Column(Integer)
    total_fats = Column(Integer)
    
    shopping_list = Column(JSON)  # ["product": "amount", ...]
    
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="meal_plans")

class WorkoutPlan(Base):
    __tablename__ = "workout_plans"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    week_number = Column(Integer)
    day_number = Column(Integer)  # 1-7
    
    workout_type = Column(String(50))  # "strength", "cardio", "mixed", "rest"
    duration_minutes = Column(Integer)
    difficulty = Column(String(20))  # "beginner", "intermediate", "advanced"
    
    exercises = Column(JSON)  # [{"name": "...", "sets": 3, "reps": 12, "rest": 60}, ...]
    
    calories_burned = Column(Integer)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="workouts")

class DailyCheckIn(Base):
    __tablename__ = "daily_checkins"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime, default=datetime.utcnow)
    
    # Morning check-in
    morning_weight = Column(Float, nullable=True)
    sleep_hours = Column(Float, nullable=True)
    mood = Column(String(20), nullable=True)  # "great", "good", "normal", "bad"
    
    # Day tracking
    water_ml = Column(Integer, default=0)
    steps = Column(Integer, default=0)
    workout_completed = Column(Boolean, default=False)
    
    # Food tracking
    breakfast_photo = Column(String(255), nullable=True)  # S3 URL
    lunch_photo = Column(String(255), nullable=True)
    dinner_photo = Column(String(255), nullable=True)
    snack_photos = Column(JSON, default=list)
    
    estimated_calories = Column(Integer, nullable=True)
    adherence_score = Column(Integer, nullable=True)  # 0-100
    
    # Evening reflection
    daily_notes = Column(Text, nullable=True)
    challenges = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="check_ins")

class WeightLog(Base):
    __tablename__ = "weight_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    weight = Column(Float)
    date = Column(DateTime, default=datetime.utcnow)
    
    # Опциональные измерения
    waist_cm = Column(Float, nullable=True)
    hips_cm = Column(Float, nullable=True)
    chest_cm = Column(Float, nullable=True)
    
    photo_url = Column(String(255), nullable=True)  # Progress photo S3 URL
    
    user = relationship("User", back_populates="weight_logs")

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    amount = Column(Integer)  # в копейках
    currency = Column(String(3), default="RUB")
    subscription_type = Column(String(20))  # "monthly", "quarterly", "yearly"
    
    provider = Column(String(50))  # "stripe", "yukassa", etc.
    provider_payment_id = Column(String(255), unique=True)
    
    status = Column(String(20))  # "pending", "succeeded", "failed", "refunded"
    
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="payments")