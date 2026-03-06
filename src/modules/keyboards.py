from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру главного меню пользователя.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🧑 Профиль",
                    callback_data="menu_profile",
                ),
                InlineKeyboardButton(
                    text="👥 Команда",
                    callback_data="menu_team",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🏆 Турниры",
                    callback_data="menu_tournaments",
                ),
                InlineKeyboardButton(
                    text="📊 Рейтинги",
                    callback_data="menu_ratings",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎁 Бонусы",
                    callback_data="menu_bonuses",
                ),
                InlineKeyboardButton(
                    text="💰 Кошелёк (CD токен)",
                    callback_data="menu_wallet",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎉 Акции и розыгрыши",
                    callback_data="menu_promotions",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🤝 Пригласи друга",
                    callback_data="menu_invite",
                ),
                InlineKeyboardButton(
                    text="❓ Поддержка",
                    callback_data="menu_support",
                ),
            ],
        ],
    )
    return keyboard
