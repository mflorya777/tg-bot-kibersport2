from aiogram import types
from aiogram.filters import Command

from src.modules.keyboards import get_main_menu_keyboard


async def start_handler(
    message: types.Message,
) -> None:
    await message.answer(
        text="Главное меню",
        reply_markup=get_main_menu_keyboard(),
    )


async def callback_handler(
    callback: types.CallbackQuery,
) -> None:
    """
    Обработчик нажатий на инлайн-кнопки главного меню.
    """
    callback_data = callback.data

    if callback_data == "menu_profile":
        await callback.answer("Профиль")
        await callback.message.edit_text(
            text="🧑 Профиль\n\nРаздел в разработке...",
            reply_markup=get_main_menu_keyboard(),
        )
    elif callback_data == "menu_team":
        await callback.answer("Команда")
        await callback.message.edit_text(
            text="👥 Команда\n\nРаздел в разработке...",
            reply_markup=get_main_menu_keyboard(),
        )
    elif callback_data == "menu_tournaments":
        await callback.answer("Турниры")
        await callback.message.edit_text(
            text="🏆 Турниры\n\nРаздел в разработке...",
            reply_markup=get_main_menu_keyboard(),
        )
    elif callback_data == "menu_ratings":
        await callback.answer("Рейтинги")
        await callback.message.edit_text(
            text="📊 Рейтинги\n\nРаздел в разработке...",
            reply_markup=get_main_menu_keyboard(),
        )
    elif callback_data == "menu_bonuses":
        await callback.answer("Бонусы")
        await callback.message.edit_text(
            text="🎁 Бонусы\n\nРаздел в разработке...",
            reply_markup=get_main_menu_keyboard(),
        )
    elif callback_data == "menu_wallet":
        await callback.answer("Кошелёк")
        await callback.message.edit_text(
            text="💰 Кошелёк (CD токен)\n\nРаздел в разработке...",
            reply_markup=get_main_menu_keyboard(),
        )
    elif callback_data == "menu_promotions":
        await callback.answer("Акции и розыгрыши")
        await callback.message.edit_text(
            text="🎉 Акции и розыгрыши\n\nРаздел в разработке...",
            reply_markup=get_main_menu_keyboard(),
        )
    elif callback_data == "menu_invite":
        await callback.answer("Пригласи друга")
        await callback.message.edit_text(
            text="🤝 Пригласи друга\n\nРаздел в разработке...",
            reply_markup=get_main_menu_keyboard(),
        )
    elif callback_data == "menu_support":
        await callback.answer("Поддержка")
        await callback.message.edit_text(
            text="❓ Поддержка\n\nРаздел в разработке...",
            reply_markup=get_main_menu_keyboard(),
        )
