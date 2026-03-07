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
    # Регистрируем обработчики сообщений
    # В aiogram 3.x обработчики вызываются последовательно
    # Каждый обработчик проверяет свое состояние и если не подходит - просто возвращается
    # Порядок важен - более специфичные обработчики должны быть первыми
    
    # Сначала обработчики, которые проверяют состояние через словари
    # (они должны быть первыми, чтобы не блокировать друг друга)
    # Важно: порядок регистрации определяет порядок вызова
    # В aiogram 3.x обработчики вызываются в порядке регистрации
    # Если один обработчик делает return, следующий должен вызываться
    print("[DEBUG] Регистрация обработчиков сообщений...")
    
    # Импортируем словари для проверки состояния
    from src.modules.handlers import (
        _waiting_team_data,
        _waiting_promocode,
        _waiting_support_question,
        _tournament_creation_data,
    )
    
    # Создаем один общий обработчик, который проверяет все состояния
    async def unified_message_handler(message: types.Message):
        """Общий обработчик, который проверяет все состояния и вызывает соответствующие функции"""
        user_id = message.from_user.id
        
        print(f"[DEBUG] >>> unified_message_handler ВЫЗВАН для пользователя {user_id}")
        print(f"[DEBUG] Состояния: team={_waiting_team_data.get(user_id, False)}, "
              f"promocode={_waiting_promocode.get(user_id, False)}, "
              f"support={_waiting_support_question.get(user_id, False)}, "
              f"tournament={user_id in _tournament_creation_data}")
        
        # Проверяем состояние промокода
        if _waiting_promocode.get(user_id, False):
            print(f"[DEBUG] >>> Вызываем promocode_message_handler для пользователя {user_id}")
            await promocode_message_handler(message)
            return
        
        # Проверяем состояние команды
        if _waiting_team_data.get(user_id, False):
            print(f"[DEBUG] >>> Вызываем team_create_message_handler для пользователя {user_id}")
            await team_create_message_handler(message)
            return
        
        # Проверяем состояние поддержки
        if _waiting_support_question.get(user_id, False):
            print(f"[DEBUG] >>> Вызываем support_question_message_handler для пользователя {user_id}")
            await support_question_message_handler(message)
            return
        
        # Проверяем состояние создания турнира
        if user_id in _tournament_creation_data:
            print(f"[DEBUG] >>> Вызываем tournament_create_message_handler для пользователя {user_id}")
            await tournament_create_message_handler(message)
            return
        
        # Проверяем состояние поиска пользователя в админ-панели
        from src.modules.handlers import _waiting_user_search, _waiting_token_amount, _waiting_team_search
        if _waiting_user_search.get(user_id, False):
            print(f"[DEBUG] >>> Вызываем admin_user_search_message_handler для пользователя {user_id}")
            from src.modules.handlers import admin_user_search_message_handler
            await admin_user_search_message_handler(message)
            return
        
        # Проверяем состояние ожидания суммы токенов
        if user_id in _waiting_token_amount:
            print(f"[DEBUG] >>> Вызываем admin_token_amount_message_handler для пользователя {user_id}")
            from src.modules.handlers import admin_token_amount_message_handler
            await admin_token_amount_message_handler(message)
            return
        
        # Проверяем состояние поиска команды в админ-панели
        if _waiting_team_search.get(user_id, False):
            print(f"[DEBUG] >>> Вызываем admin_team_search_message_handler для пользователя {user_id}")
            from src.modules.handlers import admin_team_search_message_handler
            await admin_team_search_message_handler(message)
            return
        
        # Если ни одно состояние не активно, ничего не делаем
        print(f"[DEBUG] >>> unified_message_handler: нет активных состояний для пользователя {user_id}")
    
    # Регистрируем единый обработчик
    dp.message.register(unified_message_handler)
    print("[DEBUG] unified_message_handler зарегистрирован")
    
    # Добавляем общий обработчик для отладки (в конце, чтобы не мешать другим)
    async def debug_message_handler(message: types.Message):
        """Общий обработчик для отладки - логирует все сообщения"""
        print(f"[DEBUG] >>> debug_message_handler ВЫЗВАН (последний)")
        if message.text and not message.text.startswith("/"):
            user_id = message.from_user.id
            print(
                f"[DEBUG] Получено сообщение от {user_id}: "
                f"'{message.text[:50]}' | "
                f"waiting_team={_waiting_team_data.get(user_id, False)}, "
                f"waiting_promocode={_waiting_promocode.get(user_id, False)}, "
                f"waiting_support={_waiting_support_question.get(user_id, False)}, "
                f"creating_tournament={user_id in _tournament_creation_data}"
            )
        # Этот обработчик всегда должен вызываться последним
        # Он не блокирует другие обработчики, так как просто логирует
    
    dp.message.register(debug_message_handler)
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
        | F.data.startswith("bonus_")
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
