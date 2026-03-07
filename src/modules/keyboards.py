from typing import Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from src.models.mongo_models import Team, Tournament
from src.config import MINI_APP_URL


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
                web_app=WebAppInfo(url=MINI_APP_URL),
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


def get_tournaments_list_keyboard(
    tournaments: Optional[list] = None,
    current_filter: str = "all",
    current_game: Optional[str] = None,
    available_games: Optional[list[str]] = None,
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для списка турниров с фильтрами.
    
    Args:
        current_filter: Текущий фильтр (all, registration_open, in_progress, completed)
        current_game: Текущая выбранная игра (опционально)
        available_games: Список доступных игр для фильтрации
    """
    keyboard_rows = []
    
    # Фильтры по статусу (вертикально, друг над другом)
    keyboard_rows.append([
        InlineKeyboardButton(
            text="✅ Все" if current_filter == "all" else "Все",
            callback_data="tournaments_filter_all",
        ),
    ])
    keyboard_rows.append([
        InlineKeyboardButton(
            text="✅ Открыта регистрация" if current_filter == "registration_open" else "Открыта регистрация",
            callback_data="tournaments_filter_registration_open",
        ),
    ])
    keyboard_rows.append([
        InlineKeyboardButton(
            text="✅ Идёт" if current_filter == "in_progress" else "Идёт",
            callback_data="tournaments_filter_in_progress",
        ),
    ])
    keyboard_rows.append([
        InlineKeyboardButton(
            text="✅ Завершён" if current_filter == "completed" else "Завершён",
            callback_data="tournaments_filter_completed",
        ),
    ])
    
    # Фильтр по игре (если игр несколько)
    if available_games and len(available_games) > 1:
        game_buttons = []
        for game in available_games[:4]:  # Максимум 4 кнопки
            is_selected = current_game == game
            game_buttons.append(
                InlineKeyboardButton(
                    text=f"{'✅ ' if is_selected else ''}{game}",
                    callback_data=f"tournaments_filter_game_{game}",
                ),
            )
        if len(game_buttons) > 0:
            keyboard_rows.append(game_buttons)
    
    # Кнопки для каждого турнира
    if tournaments:
        keyboard_rows.append([])  # Пустая строка для разделения
        for tournament in tournaments[:10]:  # Максимум 10 турниров
            status_emoji = {
                "registration_open": "✅",
                "in_progress": "🔄",
                "completed": "🏁",
            }
            emoji = status_emoji.get(tournament.status.value, "🏆")
            format_emoji = "👤" if tournament.format.value == "solo" else "👥"
            
            keyboard_rows.append([
                InlineKeyboardButton(
                    text=f"{emoji} {tournament.name} {format_emoji}",
                    callback_data=f"tournament_view_{tournament.id}",
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


def get_tournament_card_keyboard(
    tournament_id: str,
    tournament_status: str,
    is_participant: bool = False,
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для карточки турнира.
    
    Args:
        tournament_id: ID турнира
        tournament_status: Статус турнира
        is_participant: Участвует ли пользователь в турнире
    """
    keyboard_rows = []
    
    # Кнопка вступления (только если открыта регистрация и пользователь не участвует)
    if tournament_status == "registration_open" and not is_participant:
        keyboard_rows.append([
            InlineKeyboardButton(
                text="✅ Вступить",
                callback_data=f"tournament_join_{tournament_id}",
            ),
        ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="📋 Правила",
            callback_data=f"tournament_rules_{tournament_id}",
        ),
        InlineKeyboardButton(
            text="👥 Участники/Команды",
            callback_data=f"tournament_participants_{tournament_id}",
        ),
    ])
    
    # Кнопка таблицы результатов (только если турнир идёт или завершён)
    if tournament_status in ("in_progress", "completed"):
        keyboard_rows.append([
            InlineKeyboardButton(
                text="📊 Таблица результатов",
                callback_data=f"tournament_results_{tournament_id}",
            ),
        ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="tournaments_list",
        ),
    ])
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_rows,
    )
    return keyboard


def get_tournament_join_confirm_keyboard(
    tournament_id: str,
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для подтверждения участия в турнире (соло).
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить",
                    callback_data=f"tournament_confirm_{tournament_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=f"tournament_view_{tournament_id}",
                ),
            ],
        ],
    )
    return keyboard


def get_tournament_team_select_keyboard(
    tournament_id: str,
    user_teams: list[Team],
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для выбора команды при вступлении в командный турнир.
    
    Args:
        tournament_id: ID турнира
        user_teams: Список команд пользователя
    """
    keyboard_rows = []
    
    for team in user_teams:
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"{team.name} ({team.tag})",
                callback_data=f"tournament_join_team_{tournament_id}_{team.id}",
            ),
        ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"tournament_view_{tournament_id}",
        ),
    ])
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_rows,
    )
    return keyboard


def get_admin_tournaments_list_keyboard() -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для списка турниров в админ-панели.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Создать турнир",
                    callback_data="admin_tournament_create",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="menu_admin",
                ),
            ],
        ],
    )
    return keyboard


def get_admin_tournament_manage_keyboard(
    tournament_id: str,
    has_confirmation: bool = False,
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для управления турниром в админ-панели.
    
    Args:
        tournament_id: ID турнира
        has_confirmation: Есть ли подтверждение заявок на вступление
    """
    keyboard_rows = []
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="👥 Участники/Команды",
            callback_data=f"admin_tournament_participants_{tournament_id}",
        ),
    ])
    
    if has_confirmation:
        keyboard_rows.append([
            InlineKeyboardButton(
                text="🧾 Заявки на вступление",
                callback_data=f"admin_tournament_requests_{tournament_id}",
            ),
        ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="🧮 Результаты",
            callback_data=f"admin_tournament_results_{tournament_id}",
        ),
        InlineKeyboardButton(
            text="📊 Опубликовать таблицу",
            callback_data=f"admin_tournament_publish_{tournament_id}",
        ),
    ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="📣 Сообщение участникам",
            callback_data=f"admin_tournament_message_{tournament_id}",
        ),
    ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="🛑 Закрыть регистрацию",
            callback_data=f"admin_tournament_close_reg_{tournament_id}",
        ),
        InlineKeyboardButton(
            text="🏁 Завершить турнир",
            callback_data=f"admin_tournament_finish_{tournament_id}",
        ),
    ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="admin_tournaments",
        ),
    ])
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_rows,
    )
    return keyboard


def get_tournament_format_keyboard() -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для выбора формата турнира.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 Соло",
                    callback_data="tournament_create_format_solo",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="👥 Команды",
                    callback_data="tournament_create_format_team",
                ),
            ],
        ],
    )
    return keyboard


def get_tournament_join_type_keyboard() -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для выбора типа вступления в турнир.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌐 Все",
                    callback_data="tournament_create_join_all",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📩 По приглашению",
                    callback_data="tournament_create_join_invite",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✅ Только подтверждённые команды",
                    callback_data="tournament_create_join_confirmed",
                ),
            ],
        ],
    )
    return keyboard


def get_tournament_team_scoring_keyboard() -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для выбора формулы подсчёта очков команды.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Сумма",
                    callback_data="tournament_create_scoring_sum",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🏆 Топ-N",
                    callback_data="tournament_create_scoring_topn",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📊 Среднее",
                    callback_data="tournament_create_scoring_avg",
                ),
            ],
        ],
    )
    return keyboard


def get_tournament_review_keyboard() -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для проверки данных турнира перед публикацией.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Опубликовать",
                    callback_data="tournament_create_publish",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Изменить",
                    callback_data="tournament_create_edit",
                ),
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data="tournament_create_cancel",
                ),
            ],
        ],
    )
    return keyboard
