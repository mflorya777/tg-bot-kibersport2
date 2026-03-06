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


def get_profile_keyboard() -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для экрана профиля.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Изменить профиль",
                    callback_data="profile_edit",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📎 Привязать соцсети",
                    callback_data="profile_social",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔒 Настройки приватности",
                    callback_data="profile_privacy",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="menu_back",
                ),
            ],
        ],
    )
    return keyboard


def get_team_no_team_keyboard() -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для пользователя без команды.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Создать команду",
                    callback_data="team_create",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔎 Найти команду",
                    callback_data="team_search",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📩 Ввести код-приглашение",
                    callback_data="team_join_code",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="menu_back",
                ),
            ],
        ],
    )
    return keyboard


def get_team_keyboard(
    is_captain: bool = False,
    is_admin: bool = False,
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для пользователя с командой.
    
    Args:
        is_captain: Является ли пользователь капитаном команды
        is_admin: Является ли пользователь админом/супер-админом
    """
    keyboard_rows = []
    
    # Кнопки доступные капитану и админу
    if is_captain or is_admin:
        keyboard_rows.append([
            InlineKeyboardButton(
                text="👤 Назначить капитана",
                callback_data="team_set_captain",
            ),
        ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="➕ Пригласить игрока",
            callback_data="team_invite",
        ),
    ])
    
    # Кнопка управления заявками только для капитана
    if is_captain:
        keyboard_rows.append([
            InlineKeyboardButton(
                text="🛠 Управление заявками",
                callback_data="team_manage_requests",
            ),
        ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="❌ Покинуть команду",
            callback_data="team_leave",
        ),
    ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="menu_back",
        ),
    ])
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_rows,
    )
    return keyboard
