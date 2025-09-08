from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from api.routers import webhook, users, analytics, admin
from core.database import init_db
from config import settings

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    await init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(
    title="Fitness Bot API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(webhook.router, prefix="/webhook", tags=["webhook"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

@app.get("/")
async def root():
    return {"message": "Fitness Bot API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}