from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu_keyboard(
    show_admin: bool = False,
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру главного меню пользователя.
    
    Args:
        show_admin: Показывать ли кнопку "Админка" (для админов, менеджеров и супер-админов)
    """
    keyboard_rows = [
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
    ]
    
    if show_admin:
        keyboard_rows.append([
            InlineKeyboardButton(
                text="⚙️ Админка",
                callback_data="menu_admin",
            ),
        ])
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_rows,
    )
    return keyboard


def get_admin_panel_keyboard(
    is_super_admin: bool = False,
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру админ-панели.
    
    Args:
        is_super_admin: Является ли пользователь супер-админом
    """
    keyboard_rows = [
        [
            InlineKeyboardButton(
                text="🏆 Турниры",
                callback_data="admin_tournaments",
            ),
            InlineKeyboardButton(
                text="✅ Результаты",
                callback_data="admin_results",
            ),
        ],
        [
            InlineKeyboardButton(
                text="👥 Пользователи",
                callback_data="admin_users",
            ),
            InlineKeyboardButton(
                text="🧑‍🤝‍🧑 Команды",
                callback_data="admin_teams",
            ),
        ],
        [
            InlineKeyboardButton(
                text="📊 Рейтинги",
                callback_data="admin_ratings",
            ),
            InlineKeyboardButton(
                text="💰 CD токен и бонусы",
                callback_data="admin_wallet_bonuses",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🎉 Акции и розыгрыши",
                callback_data="admin_promotions",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🤝 Рефералка",
                callback_data="admin_referral",
            ),
            InlineKeyboardButton(
                text="📣 Рассылка",
                callback_data="admin_broadcast",
            ),
        ],
    ]
    
    if is_super_admin:
        keyboard_rows.append([
            InlineKeyboardButton(
                text="🧾 Журнал действий",
                callback_data="admin_audit",
            ),
        ])
        keyboard_rows.append([
            InlineKeyboardButton(
                text="⚙️ Настройки",
                callback_data="admin_settings",
            ),
        ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="◀️ Назад в меню",
            callback_data="menu_back",
        ),
    ])
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_rows,
    )
    return keyboard
