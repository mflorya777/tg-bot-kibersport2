#!/usr/bin/env python
"""
Запуск FastAPI сервера для API мини-приложений.
"""
import asyncio
import logging
import uvicorn
from dotenv import load_dotenv

from src.config import MongoConfig
from src.clients.mongo import MongoClient
from src.api.app import create_app


load_dotenv("local.env")

_LOG = logging.getLogger("kibersport-api")


async def main():
    """
    Основная функция запуска API сервера.
    """
    # Инициализация MongoDB клиента
    mongo_config = MongoConfig()
    mongo_client = MongoClient(mongo_config)
    
    # Проверка подключения к БД
    if not await mongo_client.ping():
        _LOG.warning(
            "Не удалось подключиться к MongoDB. API будет работать с ограниченным функционалом.",
        )
    
    # Создание FastAPI приложения
    app = create_app(mongo_client)
    
    # Запуск сервера
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    asyncio.run(main())
