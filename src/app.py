import logging
from functools import partial

from aiogram import (
    Bot,
    Dispatcher,
    F,
    types,
)
from aiogram.filters import Command

from src.config import TOKEN
from src.modules.handlers import (
    start_handler,
    callback_handler,
    admin_callback_handler,
)


_LOG = logging.getLogger("woman-tg-bot")

dp = Dispatcher()


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
    dp.callback_query.register(
        callback_handler,
        F.data.startswith("menu_"),
    )
    dp.callback_query.register(
        admin_callback_handler,
        F.data.startswith("admin_"),
    )


async def main() -> None:
    """
    Функция запуска бота.
    """

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
