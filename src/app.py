import logging
from functools import partial
from dotenv import load_dotenv

from aiogram import (
    Bot,
    Dispatcher,
    F,
    types,
)
from aiogram.filters import Command

from src.config import TOKEN


_LOG = logging.getLogger("woman-tg-bot")

load_dotenv()
dp = Dispatcher()


async def register_handlers(
    dp: Dispatcher,
):
    """
    Функция регистрации всех хэндлеров.
    """
    pass


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
