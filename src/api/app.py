from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.router import router, set_mongo_client
from src.clients.mongo import MongoClient
from src.config import MongoConfig


def create_app(mongo_client: MongoClient) -> FastAPI:
    """
    Создает и настраивает FastAPI приложение.
    
    Args:
        mongo_client: Экземпляр MongoClient для работы с БД
    
    Returns:
        Настроенное FastAPI приложение
    """
    app = FastAPI(
        title="Kibersport Bot API",
        description="API для мини-приложений Telegram бота Kibersport",
        version="1.0.0",
    )
    
    # Настраиваем CORS для работы с Telegram WebApp
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # В продакшене лучше указать конкретные домены
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Устанавливаем MongoClient для роутера
    set_mongo_client(mongo_client)
    
    # Подключаем роутер
    app.include_router(router)
    
    return app
