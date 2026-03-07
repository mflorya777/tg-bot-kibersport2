import logging
from functools import partial

from aiogram import (
    Bot,
    Dispatcher,
    F,
    types,
)
from aiogram.filters import Command

from src.config import TOKEN, MongoConfig
from src.clients.mongo import MongoClient
from src.modules.handlers import (
    start_handler,
    callback_handler,
    admin_callback_handler,
    team_create_message_handler,
    tournament_create_message_handler,
    support_question_message_handler,
    promocode_message_handler,
    set_mongo_client,
)


_LOG = logging.getLogger("woman-tg-bot")

dp = Dispatcher()

# Инициализация MongoDB клиента
mongo_config = MongoConfig()
mongo_client = MongoClient(mongo_config)


async def register_handlers(
    dp: Dispatcher,
):
    """
    Функция регистрации всех хэндлеров.
    """
    dp.message.register(
        start_handler,
        Command("start"),
    )
    # Регистрируем обработчики в порядке приоритета:
    # 1. Обработчик промокодов (проверяется первым)
    # 2. Обработчик вопросов в поддержку
    # 3. Обработчик создания турнира
    # 4. Обработчик создания команды
    dp.message.register(
        promocode_message_handler,
    )
    dp.message.register(
        support_question_message_handler,
    )
    dp.message.register(
        tournament_create_message_handler,
    )
    dp.message.register(
        team_create_message_handler,
    )
    dp.callback_query.register(
        callback_handler,
        F.data.startswith("menu_")
        | F.data.startswith("profile_")
        | F.data.startswith("team_")
        | F.data.startswith("tournaments_")
        | F.data.startswith("ratings_")
        | F.data.startswith("support_")
        | F.data.startswith("faq_")
        | F.data.startswith("wallet_")
        | (F.data.startswith("tournament_") & ~F.data.startswith("tournament_create_") & ~F.data.startswith("tournament_join_") & ~F.data.startswith("tournament_confirm_")),
    )
    dp.callback_query.register(
        admin_callback_handler,
        F.data.startswith("admin_") | F.data.startswith("tournament_create_"),
    )


async def main() -> None:
    """
    Функция запуска бота.
    """
    # Устанавливаем MongoClient в handlers
    set_mongo_client(mongo_client)
    
    # Проверяем подключение к MongoDB
    is_connected = await mongo_client.ping()
    if is_connected:
        _LOG.info(
            f"Подключение к MongoDB успешно: {mongo_config.mongo_host}:{mongo_config.mongo_port}/{mongo_config.mongo_db_name}",
        )
    else:
        _LOG.warning(
            f"Не удалось подключиться к MongoDB ({mongo_config.mongo_host}:{mongo_config.mongo_port})",
        )
        _LOG.warning(
            "Бот будет работать без БД. Все пользователи будут иметь роль USER по умолчанию.",
        )

    await register_handlers(
        dp,
    )
    bot = Bot(
        token=TOKEN,
    )
    _LOG.info(
        "Удаляю webhook (если активен) перед запуском long polling",
    )
    await bot.delete_webhook(
        drop_pending_updates=True,
    )
    _LOG.info(
        "Бот запущен",
    )
    await dp.start_polling(
        bot,
    )
