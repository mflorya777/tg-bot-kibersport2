from typing import Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from src.models.mongo_models import (
    Team,
    Tournament,
    Match,
    Promocode,
    TransactionReason,
    TransactionType,
    Giveaway,
    GiveawayStatus,
)
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
    results_published: bool = False,
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для карточки турнира.
    
    Args:
        tournament_id: ID турнира
        tournament_status: Статус турнира
        is_participant: Участвует ли пользователь в турнире
        results_published: Опубликованы ли результаты турнира
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
    
    # Кнопка таблицы результатов (только если результаты опубликованы)
    if results_published:
        keyboard_rows.append([
            InlineKeyboardButton(
                text="📊 Результаты",
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


def get_ratings_type_keyboard() -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для выбора типа рейтинга.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🧑 Рейтинг игроков",
                    callback_data="ratings_players",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="👥 Рейтинг команд",
                    callback_data="ratings_teams",
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


def get_ratings_filter_keyboard(
    rating_type: str,
    current_filter: str = "all_time",
    current_tournament: Optional[str] = None,
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для фильтров рейтинга.
    
    Args:
        rating_type: Тип рейтинга (players или teams)
        current_filter: Текущий фильтр (all_time, season, month, tournament)
        current_tournament: ID текущего выбранного турнира (если фильтр по турниру)
    """
    keyboard_rows = []
    
    # Фильтры по времени
    keyboard_rows.append([
        InlineKeyboardButton(
            text="✅ За всё время" if current_filter == "all_time" else "За всё время",
            callback_data=f"ratings_filter_{rating_type}_all_time",
        ),
    ])
    keyboard_rows.append([
        InlineKeyboardButton(
            text="✅ За сезон" if current_filter == "season" else "За сезон",
            callback_data=f"ratings_filter_{rating_type}_season",
        ),
    ])
    keyboard_rows.append([
        InlineKeyboardButton(
            text="✅ За месяц" if current_filter == "month" else "За месяц",
            callback_data=f"ratings_filter_{rating_type}_month",
        ),
    ])
    keyboard_rows.append([
        InlineKeyboardButton(
            text="✅ По турниру" if current_filter == "tournament" else "По турниру",
            callback_data=f"ratings_filter_{rating_type}_tournament",
        ),
    ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="🔎 Найти себя",
            callback_data=f"ratings_find_{rating_type}",
        ),
    ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="ratings_type",
        ),
    ])
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_rows,
    )
    return keyboard


def get_ratings_tournament_select_keyboard(
    rating_type: str,
    tournaments: list[Tournament],
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для выбора турнира при фильтрации рейтинга.
    
    Args:
        rating_type: Тип рейтинга (players или teams)
        tournaments: Список турниров для выбора
    """
    keyboard_rows = []
    
    for tournament in tournaments[:10]:  # Максимум 10 турниров
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"🏆 {tournament.name}",
                callback_data=f"ratings_tournament_{rating_type}_{tournament.id}",
            ),
        ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"ratings_{rating_type}",
        ),
    ])
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_rows,
    )
    return keyboard


def get_support_keyboard() -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для раздела поддержки.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Задать вопрос",
                    callback_data="support_ask",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❓ Частые вопросы",
                    callback_data="support_faq",
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


def get_faq_keyboard() -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру с частыми вопросами.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❓ Тестовый вопрос 1",
                    callback_data="faq_1",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❓ Тестовый вопрос 2",
                    callback_data="faq_2",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❓ Тестовый вопрос 3",
                    callback_data="faq_3",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❓ Тестовый вопрос 4",
                    callback_data="faq_4",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❓ Тестовый вопрос 5",
                    callback_data="faq_5",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❓ Тестовый вопрос 6",
                    callback_data="faq_6",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="menu_support",
                ),
            ],
        ],
    )
    return keyboard


def get_wallet_keyboard() -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для кошелька.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📜 История операций",
                    callback_data="wallet_history",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎟 Потратить токены",
                    callback_data="wallet_spend",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🧾 Ввести промокод",
                    callback_data="wallet_promocode",
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


def get_bonuses_keyboard(
    daily_bonus_available: bool = False,
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для экрана бонусов.
    
    Args:
        daily_bonus_available: Доступен ли ежедневный бонус
    """
    keyboard_rows = []
    
    # Ежедневный бонус
    if daily_bonus_available:
        keyboard_rows.append([
            InlineKeyboardButton(
                text="🎁 Забрать ежедневный бонус",
                callback_data="bonus_daily_claim",
            ),
        ])
    else:
        keyboard_rows.append([
            InlineKeyboardButton(
                text="⏰ Ежедневный бонус (уже получен)",
                callback_data="bonus_daily_info",
            ),
        ])
    
    # Реферальный бонус
    keyboard_rows.append([
        InlineKeyboardButton(
            text="👥 Бонус за приглашение друга",
            callback_data="bonus_referral",
        ),
    ])
    
    # Задания
    keyboard_rows.append([
        InlineKeyboardButton(
            text="📋 Задания",
            callback_data="bonus_quests",
        ),
    ])
    
    # Назад
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


def get_admin_users_search_keyboard() -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для поиска пользователей в админ-панели.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_back",
                ),
            ],
        ],
    )
    return keyboard


def get_admin_user_card_keyboard(
    user_id: int,
    is_super_admin: bool = False,
    is_banned: bool = False,
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для карточки пользователя в админ-панели.
    
    Args:
        user_id: Telegram user_id пользователя
        is_super_admin: Является ли текущий пользователь супер-админом
        is_banned: Забанен ли пользователь
    """
    keyboard_rows = [
        [
            InlineKeyboardButton(
                text="➕ Начислить CD токен",
                callback_data=f"admin_user_add_tokens_{user_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="➖ Списать CD токен",
                callback_data=f"admin_user_remove_tokens_{user_id}",
            ),
        ],
    ]
    
    # Кнопка бана/разбана
    if is_banned:
        keyboard_rows.append([
            InlineKeyboardButton(
                text="✅ Снять ограничение",
                callback_data=f"admin_user_unban_{user_id}",
            ),
        ])
    else:
        keyboard_rows.append([
            InlineKeyboardButton(
                text="🚫 Ограничить доступ (бан)",
                callback_data=f"admin_user_ban_{user_id}",
            ),
        ])
    
    # Только супер-админ может назначать роли
    if is_super_admin:
        keyboard_rows.append([
            InlineKeyboardButton(
                text="🎭 Назначить роль",
                callback_data=f"admin_user_role_{user_id}",
            ),
        ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="admin_users",
        ),
    ])
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_rows,
    )
    return keyboard


def get_admin_user_role_keyboard(
    user_id: int,
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для выбора роли пользователя.
    
    Args:
        user_id: Telegram user_id пользователя
    """
    from src.models.user_roles import UserRole
    
    keyboard_rows = [
        [
            InlineKeyboardButton(
                text="👤 Пользователь",
                callback_data=f"admin_user_set_role_{user_id}_USER",
            ),
        ],
        [
            InlineKeyboardButton(
                text="👔 Менеджер",
                callback_data=f"admin_user_set_role_{user_id}_MANAGER",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🛡️ Админ",
                callback_data=f"admin_user_set_role_{user_id}_ADMIN",
            ),
        ],
        [
            InlineKeyboardButton(
                text="👑 Супер-админ",
                callback_data=f"admin_user_set_role_{user_id}_SUPER_ADMIN",
            ),
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"admin_user_card_{user_id}",
            ),
        ],
    ]
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_rows,
    )
    return keyboard


def get_admin_teams_search_keyboard() -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для поиска команд в админ-панели.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_back",
                ),
            ],
        ],
    )
    return keyboard


def get_admin_team_card_keyboard(
    team_id: str,
    is_banned: bool = False,
    captain_confirmed: bool = False,
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для карточки команды в админ-панели.
    
    Args:
        team_id: ID команды
        is_banned: Забанена ли команда
        captain_confirmed: Подтвержден ли капитан
    """
    keyboard_rows = []
    
    # Подтверждение капитана
    if not captain_confirmed:
        keyboard_rows.append([
            InlineKeyboardButton(
                text="✅ Подтвердить капитана",
                callback_data=f"admin_team_confirm_captain_{team_id}",
            ),
        ])
    
    # Блокировка команды
    if is_banned:
        keyboard_rows.append([
            InlineKeyboardButton(
                text="✅ Разблокировать команду",
                callback_data=f"admin_team_unban_{team_id}",
            ),
        ])
    else:
        keyboard_rows.append([
            InlineKeyboardButton(
                text="🚫 Заблокировать команду",
                callback_data=f"admin_team_ban_{team_id}",
            ),
        ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="admin_teams",
        ),
    ])
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_rows,
    )
    return keyboard


def get_admin_ratings_keyboard() -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для админ-панели рейтингов.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Обновить рейтинг",
                    callback_data="admin_ratings_recalculate",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📅 Выбрать период",
                    callback_data="admin_ratings_period",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Настройка правил",
                    callback_data="admin_ratings_rules",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_back",
                ),
            ],
        ],
    )
    return keyboard


def get_admin_ratings_period_keyboard() -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для выбора периода рейтинга.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📅 За всё время",
                    callback_data="admin_ratings_period_all_time",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📅 За сезон",
                    callback_data="admin_ratings_period_season",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📅 За месяц",
                    callback_data="admin_ratings_period_month",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_ratings",
                ),
            ],
        ],
    )
    return keyboard


def get_admin_ratings_rules_keyboard() -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для настройки правил рейтинга.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 Рейтинг игроков",
                    callback_data="admin_ratings_rules_player",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="👥 Рейтинг команд",
                    callback_data="admin_ratings_rules_team",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_ratings",
                ),
            ],
        ],
    )
    return keyboard


def get_admin_ratings_metric_keyboard(
    rating_type: str,
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для выбора метрики рейтинга.
    
    Args:
        rating_type: Тип рейтинга (player или team)
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💀 Киллы",
                    callback_data=f"admin_ratings_metric_{rating_type}_kills",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⭐ Очки",
                    callback_data=f"admin_ratings_metric_{rating_type}_points",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_ratings_rules",
                ),
            ],
        ],
    )
    return keyboard


def get_admin_results_tournaments_keyboard(
    tournaments: list[Tournament],
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для выбора турнира при внесении результатов.
    
    Args:
        tournaments: Список турниров
    """
    keyboard_rows = []
    
    for tournament in tournaments:
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"🏆 {tournament.name}",
                callback_data=f"admin_results_tournament_{tournament.id}",
            ),
        ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="admin_back",
        ),
    ])
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_rows,
    )
    return keyboard


def get_admin_results_method_keyboard(
    tournament_id: str,
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для выбора метода внесения результатов.
    
    Args:
        tournament_id: ID турнира
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Вариант A: Итоговая цифра",
                    callback_data=f"admin_results_method_a_{tournament_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎮 Вариант B: По матчам",
                    callback_data=f"admin_results_method_b_{tournament_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_results",
                ),
            ],
        ],
    )
    return keyboard


def get_admin_results_matches_keyboard(
    tournament_id: str,
    matches: list[Match],
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для выбора матча.
    
    Args:
        tournament_id: ID турнира
        matches: Список матчей
    """
    keyboard_rows = []
    
    for match in matches:
        status = "✅" if match.is_completed else "⏳"
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"{status} {match.name}",
                callback_data=f"admin_results_match_{match.id}",
            ),
        ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="➕ Создать матч",
            callback_data=f"admin_results_create_match_{tournament_id}",
        ),
    ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"admin_results_tournament_{tournament_id}",
        ),
    ])
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_rows,
    )
    return keyboard


def get_admin_results_draft_keyboard(
    tournament_id: str,
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для черновика результатов.
    
    Args:
        tournament_id: ID турнира
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Опубликовать результаты",
                    callback_data=f"admin_results_publish_{tournament_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Исправить",
                    callback_data=f"admin_results_edit_{tournament_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=f"admin_results_tournament_{tournament_id}",
                ),
            ],
        ],
    )
    return keyboard


def get_admin_wallet_bonuses_keyboard() -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для админ-панели CD токен и бонусы.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎁 Ежедневный бонус",
                    callback_data="admin_bonus_daily_settings",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎟 Промокоды",
                    callback_data="admin_promocodes",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📝 Причины транзакций",
                    callback_data="admin_transaction_reasons",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_back",
                ),
            ],
        ],
    )
    return keyboard


def get_admin_daily_bonus_settings_keyboard(
    enabled: bool,
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для настройки ежедневного бонуса.
    
    Args:
        enabled: Включен ли ежедневный бонус
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{'✅' if enabled else '❌'} {'Выключить' if enabled else 'Включить'}",
                    callback_data=f"admin_bonus_daily_toggle",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💰 Изменить сумму",
                    callback_data="admin_bonus_daily_amount",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_wallet_bonuses",
                ),
            ],
        ],
    )
    return keyboard


def get_admin_promocodes_list_keyboard(
    promocodes: list[Promocode],
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для списка промокодов.
    
    Args:
        promocodes: Список промокодов
    """
    keyboard_rows = []
    
    for promocode in promocodes:
        status = "✅" if promocode.is_active else "❌"
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"{status} {promocode.code} ({promocode.amount} токенов)",
                callback_data=f"admin_promocode_{promocode.id}",
            ),
        ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="➕ Создать промокод",
            callback_data="admin_promocode_create",
        ),
    ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="admin_wallet_bonuses",
        ),
    ])
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_rows,
    )
    return keyboard


def get_admin_promocode_card_keyboard(
    promocode_id: str,
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для карточки промокода.
    
    Args:
        promocode_id: ID промокода
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅/❌ Активировать/Деактивировать",
                    callback_data=f"admin_promocode_toggle_{promocode_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Редактировать",
                    callback_data=f"admin_promocode_edit_{promocode_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_promocodes",
                ),
            ],
        ],
    )
    return keyboard


def get_admin_transaction_reasons_list_keyboard(
    reasons: list[TransactionReason],
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для списка причин транзакций.
    
    Args:
        reasons: Список причин
    """
    keyboard_rows = []
    
    for reason in reasons:
        status = "✅" if reason.is_active else "❌"
        type_icon = "➕" if reason.transaction_type == TransactionType.DEPOSIT else "➖"
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"{status} {type_icon} {reason.name}",
                callback_data=f"admin_transaction_reason_{reason.id}",
            ),
        ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="➕ Создать шаблон",
            callback_data="admin_transaction_reason_create",
        ),
    ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="admin_wallet_bonuses",
        ),
    ])
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_rows,
    )
    return keyboard


def get_admin_promotions_keyboard() -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для админ-панели акций и розыгрышей.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Создать розыгрыш",
                    callback_data="admin_promotion_create",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📋 Список розыгрышей",
                    callback_data="admin_promotions_list",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_back",
                ),
            ],
        ],
    )
    return keyboard


def get_admin_promotions_list_keyboard(
    promotions: list[Giveaway],
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для списка розыгрышей.
    
    Args:
        promotions: Список розыгрышей
    """
    keyboard_rows = []
    
    for promotion in promotions:
        status_icon = "✅" if promotion.status == GiveawayStatus.ACTIVE else "⏳" if promotion.status == GiveawayStatus.DRAFT else "🏁"
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"{status_icon} {promotion.name}",
                callback_data=f"admin_promotion_{promotion.id}",
            ),
        ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="admin_promotions",
        ),
    ])
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_rows,
    )
    return keyboard


def get_admin_promotion_card_keyboard(
    promotion_id: str,
    status: GiveawayStatus,
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для карточки розыгрыша.
    
    Args:
        promotion_id: ID розыгрыша
        status: Статус розыгрыша
    """
    keyboard_rows = []
    
    if status == GiveawayStatus.ACTIVE:
        keyboard_rows.append([
            InlineKeyboardButton(
                text="🏁 Определить победителей",
                callback_data=f"admin_promotion_determine_winners_{promotion_id}",
            ),
        ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="admin_promotions_list",
        ),
    ])
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_rows,
    )
    return keyboard


def get_giveaway_participation_type_keyboard() -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для выбора способа участия в розыгрыше.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💰 За CD токены",
                    callback_data="admin_promotion_type_tokens",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✅ За выполнение условия",
                    callback_data="admin_promotion_type_condition",
                ),
            ],
        ],
    )
    return keyboard


def get_admin_broadcast_keyboard() -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для админ-панели рассылки.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Всем пользователям",
                    callback_data="admin_broadcast_all",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🏆 Участникам турнира",
                    callback_data="admin_broadcast_tournament",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="👥 Менеджерам/Админам",
                    callback_data="admin_broadcast_staff",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_back",
                ),
            ],
        ],
    )
    return keyboard


def get_admin_broadcast_tournaments_keyboard(
    tournaments: list[Tournament],
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для выбора турнира при рассылке.
    
    Args:
        tournaments: Список турниров
    """
    keyboard_rows = []
    
    for tournament in tournaments:
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"🏆 {tournament.name}",
                callback_data=f"admin_broadcast_tournament_{tournament.id}",
            ),
        ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="admin_broadcast",
        ),
    ])
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_rows,
    )
    return keyboard


def get_admin_broadcast_preview_keyboard(
    broadcast_type: str,
    tournament_id: Optional[str] = None,
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для предпросмотра рассылки.
    
    Args:
        broadcast_type: Тип рассылки (all, tournament, staff)
        tournament_id: ID турнира (если тип - tournament)
    """
    keyboard_rows = []
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="✅ Отправить",
            callback_data=f"admin_broadcast_confirm_{broadcast_type}_{tournament_id or ''}",
        ),
    ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="✏️ Изменить",
            callback_data="admin_broadcast_edit",
        ),
    ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="admin_broadcast",
        ),
    ])
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_rows,
    )
    return keyboard


def get_admin_actions_log_keyboard(
    page: int = 0,
    has_next: bool = False,
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для журнала действий.
    
    Args:
        page: Номер страницы
        has_next: Есть ли следующая страница
    """
    keyboard_rows = []
    
    if page > 0:
        keyboard_rows.append([
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"admin_actions_log_page_{page - 1}",
            ),
        ])
    
    if has_next:
        keyboard_rows.append([
            InlineKeyboardButton(
                text="➡️ Вперед",
                callback_data=f"admin_actions_log_page_{page + 1}",
            ),
        ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="🔄 Обновить",
            callback_data="admin_actions_log",
        ),
    ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="admin_back",
        ),
    ])
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_rows,
    )
    return keyboard


def get_tournament_results_keyboard(
    tournament_id: str,
    is_participant: bool = False,
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для просмотра результатов турнира пользователем.
    
    Args:
        tournament_id: ID турнира
        is_participant: Участвует ли пользователь в турнире
    """
    keyboard_rows = []
    
    if is_participant:
        keyboard_rows.append([
            InlineKeyboardButton(
                text="💀 Твои киллы по матчам",
                callback_data=f"tournament_results_matches_{tournament_id}",
            ),
        ])
        keyboard_rows.append([
            InlineKeyboardButton(
                text="🏆 Итог турнира",
                callback_data=f"tournament_results_final_{tournament_id}",
            ),
        ])
        keyboard_rows.append([
            InlineKeyboardButton(
                text="👥 Очки команды",
                callback_data=f"tournament_results_team_{tournament_id}",
            ),
        ])
        keyboard_rows.append([
            InlineKeyboardButton(
                text="⚠️ Оспорить результат",
                callback_data=f"tournament_results_dispute_{tournament_id}",
            ),
        ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="📊 Общая таблица",
            callback_data=f"tournament_results_table_{tournament_id}",
        ),
    ])
    
    keyboard_rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"tournament_card_{tournament_id}",
        ),
    ])
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_rows,
    )
    return keyboard


def get_tournament_results_dispute_keyboard(
    tournament_id: str,
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для оспаривания результатов.
    
    Args:
        tournament_id: ID турнира
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=f"tournament_results_{tournament_id}",
                ),
            ],
        ],
    )
    return keyboard
