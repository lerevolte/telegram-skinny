from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Bot settings
    BOT_TOKEN: str
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost/fitness_bot"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # Webhook settings
    USE_WEBHOOK: bool = False
    WEBHOOK_URL: Optional[str] = None
    WEBHOOK_PORT: int = 8000
    
    # Payment providers
    STRIPE_TOKEN: Optional[str] = None
    YUKASSA_TOKEN: Optional[str] = None
    
    # AI Settings
    OPENAI_API_KEY: Optional[str] = None
    
    # S3 Storage
    S3_ENDPOINT: str = "https://storage.yandexcloud.net"
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET: str = "fitness-bot-storage"
    
    # Subscription prices (в копейках)
    PRICE_MONTHLY: int = 129000  # 1290 руб
    PRICE_QUARTERLY: int = 349000  # 3490 руб (скидка)
    PRICE_YEARLY: int = 1239000  # 12390 руб (скидка 20%)
    
    # Trial period
    TRIAL_DAYS: int = 7
    
    class Config:
        env_file = ".env"

settings = Settings()
