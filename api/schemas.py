from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserResponse(BaseModel):
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: str
    status: str
    subscription_end: Optional[datetime]
    daily_calories: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    height: Optional[float]
    weight: Optional[float]
    activity_level: Optional[str]
    dietary_restrictions: Optional[List[str]]
    meals_per_day: Optional[int]

class MealPlanResponse(BaseModel):
    day_number: int
    breakfast: Dict[str, Any]
    lunch: Dict[str, Any]
    dinner: Dict[str, Any]
    snack: Optional[Dict[str, Any]]
    total_calories: int
    total_protein: int
    total_carbs: int
    total_fats: int
    
    class Config:
        from_attributes = True

class ProgressResponse(BaseModel):
    start_weight: float
    current_weight: float
    target_weight: float
    weight_change: float
    days_active: int
    workouts_completed: int
    average_calories: float
    adherence_score: float
    weight_history: List[Dict[str, Any]]

class BroadcastMessage(BaseModel):
    text: str
    target_status: Optional[str] = None
    include_photo: Optional[str] = None