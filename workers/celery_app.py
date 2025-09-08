from celery import Celery
from celery.schedules import crontab
from config import settings

# Создание Celery приложения
celery_app = Celery(
    'fitness_bot',
    broker=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/1',
    backend=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/2',
    include=['workers.tasks']
)

# Конфигурация
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 минут максимум на задачу
    task_soft_time_limit=25 * 60,  # Мягкий лимит 25 минут
)

# Периодические задачи
celery_app.conf.beat_schedule = {
    # Утренние напоминания о чек-ине (8:00)
    'morning-checkin-reminder': {
        'task': 'workers.tasks.send_morning_reminder',
        'schedule': crontab(hour=8, minute=0),
    },
    
    # Напоминание о тренировке (18:00)
    'workout-reminder': {
        'task': 'workers.tasks.send_workout_reminder',
        'schedule': crontab(hour=18, minute=0),
    },
    
    # Вечерний чек-ин (21:00)
    'evening-checkin-reminder': {
        'task': 'workers.tasks.send_evening_reminder',
        'schedule': crontab(hour=21, minute=0),
    },
    
    # Еженедельная генерация планов (воскресенье 20:00)
    'weekly-meal-plan-generation': {
        'task': 'workers.tasks.generate_weekly_meal_plans',
        'schedule': crontab(hour=20, minute=0, day_of_week=0),
    },
    
    # Проверка истекающих подписок (ежедневно в 10:00)
    'check-expiring-subscriptions': {
        'task': 'workers.tasks.check_expiring_subscriptions',
        'schedule': crontab(hour=10, minute=0),
    },
    
    # Анализ прогресса и адаптация планов (ежедневно в 23:00)
    'analyze-progress': {
        'task': 'workers.tasks.analyze_user_progress',
        'schedule': crontab(hour=23, minute=0),
    },
}