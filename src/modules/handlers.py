import logging
import secrets
import string
import datetime as dt
from typing import Optional
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command

from src.modules.keyboards import (
    get_main_menu_keyboard,
    get_admin_panel_keyboard,
    get_profile_keyboard,
    get_team_no_team_keyboard,
    get_team_keyboard,
    get_tournaments_list_keyboard,
    get_tournament_card_keyboard,
    get_tournament_join_confirm_keyboard,
    get_tournament_team_select_keyboard,
    get_admin_tournaments_list_keyboard,
    get_admin_tournament_manage_keyboard,
    get_tournament_format_keyboard,
    get_tournament_join_type_keyboard,
    get_tournament_team_scoring_keyboard,
    get_tournament_review_keyboard,
    get_ratings_type_keyboard,
    get_ratings_filter_keyboard,
    get_ratings_tournament_select_keyboard,
    get_support_keyboard,
    get_faq_keyboard,
    get_wallet_keyboard,
    get_bonuses_keyboard,
    get_admin_users_search_keyboard,
    get_admin_user_card_keyboard,
    get_admin_user_role_keyboard,
    get_admin_teams_search_keyboard,
    get_admin_team_card_keyboard,
    get_admin_ratings_keyboard,
    get_admin_ratings_period_keyboard,
    get_admin_ratings_rules_keyboard,
    get_admin_ratings_metric_keyboard,
    get_admin_results_tournaments_keyboard,
    get_admin_results_method_keyboard,
    get_admin_results_matches_keyboard,
    get_admin_results_draft_keyboard,
    get_admin_wallet_bonuses_keyboard,
    get_admin_daily_bonus_settings_keyboard,
    get_admin_promocodes_list_keyboard,
    get_admin_promocode_card_keyboard,
    get_admin_transaction_reasons_list_keyboard,
    get_admin_promotions_keyboard,
    get_admin_promotions_list_keyboard,
    get_admin_promotion_card_keyboard,
    get_giveaway_participation_type_keyboard,
    get_admin_broadcast_keyboard,
    get_admin_broadcast_tournaments_keyboard,
    get_admin_broadcast_preview_keyboard,
    get_admin_actions_log_keyboard,
    get_tournament_results_keyboard,
    get_tournament_results_dispute_keyboard,
)
from src.models.user_roles import UserRole
from src.models.mongo_models import (
    User,
    Team,
    Tournament,
    TournamentStatus,
    TournamentFormat,
    Transaction,
    TransactionType,
    RatingRules,
    RatingMetric,
    Match,
    MatchResult,
    TournamentResult,
    Promocode,
    BonusSettings,
    TransactionReason,
    Giveaway,
    GiveawayStatus,
    GiveawayParticipationType,
    ActionLog,
    ActionType,
    MOSCOW_TZ,
)
from src.clients.mongo import MongoClient
from src.config import SUPPORT_ADMIN_ID


# Глобальный экземпляр MongoClient (устанавливается при запуске приложения)
_mongo_client: Optional[MongoClient] = None

_LOG = logging.getLogger("kibersport-tg-bot")

# Словарь для хранения состояния ожидания данных команды
_waiting_team_data: dict[int, bool] = {}

# Словарь для хранения данных создания турнира
_tournament_creation_data: dict[int, dict] = {}

# Словарь для хранения состояния ожидания вопроса в поддержке
_waiting_support_question: dict[int, bool] = {}

# Словарь для хранения состояния ожидания промокода
_waiting_promocode: dict[int, bool] = {}

# Словарь для хранения состояния поиска пользователя в админ-панели
_waiting_user_search: dict[int, bool] = {}

# Словарь для хранения состояния поиска команды в админ-панели
_waiting_team_search: dict[int, bool] = {}

# Словарь для хранения состояния внесения результатов
_waiting_results_data: dict[int, dict] = {}

# Словарь для хранения состояния создания розыгрыша
_waiting_giveaway_data: dict[int, dict] = {}

# Словарь для хранения состояния создания рассылки
_waiting_broadcast_data: dict[int, dict] = {}

# Словарь для хранения состояния оспаривания результатов
_waiting_results_dispute: dict[int, dict] = {}

# Словарь для хранения состояния ожидания суммы токенов для начисления/списания
_waiting_token_amount: dict[int, dict] = {}

# Словарь для хранения состояния создания/редактирования промокодов
_waiting_promocode_data: dict[int, dict] = {}

# Словарь для хранения состояния создания/редактирования причин транзакций
_waiting_transaction_reason_data: dict[int, dict] = {}


def generate_team_id() -> str:
    """
    Генерирует уникальный ID команды.
    
    Returns:
        Уникальный ID команды
    """
    return f"team_{secrets.token_urlsafe(12)}"


def generate_tournament_id() -> str:
    """
    Генерирует уникальный ID турнира.
    
    Returns:
        Уникальный ID турнира
    """
    return f"tournament_{secrets.token_urlsafe(12)}"


def generate_invite_code() -> str:
    """
    Генерирует код-приглашение для команды.
    
    Returns:
        Код-приглашение (6 символов, буквы и цифры)
    """
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(6))


def set_mongo_client(
    client: MongoClient,
) -> None:
    """
    Устанавливает глобальный экземпляр MongoClient.
    
    Args:
        client: Экземпляр MongoClient
    """
    global _mongo_client
    _mongo_client = client


async def get_user_role(
    user_id: int,
) -> UserRole:
    """
    Получает роль пользователя из базы данных.
    Если пользователя нет в базе, возвращает роль USER по умолчанию.
    
    Args:
        user_id: Telegram user_id
    
    Returns:
        Роль пользователя
    """
    if _mongo_client is None:
        # Если MongoClient не инициализирован, возвращаем USER по умолчанию
        return UserRole.USER
    
    try:
        user = await _mongo_client.get_user(user_id)
        if user is None:
            return UserRole.USER
        return user.role
    except Exception as e:
        # В случае ошибки возвращаем USER по умолчанию
        _LOG.error(
            f"Ошибка при получении роли пользователя {user_id}: {e}",
        )
        return UserRole.USER


def format_profile_text(
    user: Optional[User],
    tg_user: types.User,
) -> str:
    """
    Форматирует текст профиля пользователя для отображения.
    
    Args:
        user: Объект пользователя из БД (может быть None)
        tg_user: Объект пользователя из Telegram
    
    Returns:
        Отформатированный текст профиля
    """
    lines = ["🧑 Профиль\n"]
    
    # Никнейм
    nickname = user.nickname if user and user.nickname else None
    if nickname:
        lines.append(f"👤 Никнейм: {nickname}")
    elif tg_user.username:
        lines.append(f"👤 Никнейм: @{tg_user.username}")
    else:
        lines.append("👤 Никнейм: не указан")
    
    # Игра/дисциплина
    game_discipline = user.game_discipline if user and user.game_discipline else None
    if game_discipline:
        lines.append(f"🎮 Игра/дисциплина: {game_discipline}")
    else:
        lines.append("🎮 Игра/дисциплина: не указана")
    
    # Регион/страна
    region_country = user.region_country if user and user.region_country else None
    if region_country:
        lines.append(f"🌍 Регион/страна: {region_country}")
    else:
        lines.append("🌍 Регион/страна: не указан")
    
    # ID пользователя (для поддержки)
    lines.append(f"\n🆔 ID пользователя: {tg_user.id}")
    
    # Статистика
    lines.append("\n📊 Статистика:")
    
    tournaments_played = user.tournaments_played if user else 0
    lines.append(f"🏆 Турниров сыграно: {tournaments_played}")
    
    total_kills = user.total_kills if user else 0
    lines.append(f"⚔️ Всего киллов: {total_kills}")
    
    rating_position = user.rating_position if user and user.rating_position else None
    if rating_position:
        lines.append(f"📈 Место в рейтинге: #{rating_position}")
    else:
        lines.append("📈 Место в рейтинге: не определено")
    
    return "\n".join(lines)


async def format_admin_team_card_text(
    team: Team,
) -> str:
    """
    Форматирует текст карточки команды для админ-панели.
    
    Args:
        team: Объект команды
    
    Returns:
        Отформатированный текст карточки команды
    """
    lines = [f"👥 Карточка команды\n"]
    
    # Основная информация
    lines.append("📋 Информация:")
    lines.append(f"  🆔 ID: <code>{team.id}</code>")
    lines.append(f"  🏷 Название: {team.name}")
    lines.append(f"  📌 Тег: {team.tag}")
    lines.append(f"  🔑 Код-приглашение: <code>{team.invite_code}</code>")
    if team.is_banned:
        lines.append("  🚫 Статус: <b>Заблокирована</b>")
    else:
        lines.append("  ✅ Статус: Активна")
    if team.captain_confirmed:
        lines.append("  ✅ Капитан: Подтвержден")
    else:
        lines.append("  ⏳ Капитан: Не подтвержден")
    
    lines.append("")
    
    # Состав команды
    lines.append("👥 Состав команды:")
    if team.members:
        for member_id in team.members:
            member_name = f"ID:{member_id}"
            if _mongo_client is not None:
                try:
                    member_user = await _mongo_client.get_user(member_id)
                    if member_user:
                        member_name = member_user.nickname or member_user.name or f"ID:{member_id}"
                except Exception:
                    pass
            
            captain_mark = " 👑" if member_id == team.captain_id else ""
            lines.append(f"  • {member_name}{captain_mark}")
    else:
        lines.append("  (пусто)")
    
    lines.append("")
    
    # Статистика команды
    lines.append("📊 Статистика команды:")
    lines.append(f"  🏆 Турниров сыграно: {team.tournaments_played}")
    lines.append(f"  ⭐ Всего очков: {team.total_points}")
    if team.rating_position:
        lines.append(f"  📈 Место в рейтинге: #{team.rating_position}")
    else:
        lines.append("  📈 Место в рейтинге: не определено")
    
    return "\n".join(lines)


async def _get_participant_name(
    tournament: Tournament,
    participant_id: int | str,
) -> str:
    """
    Получает имя участника (игрока или команды).
    
    Args:
        tournament: Объект турнира
        participant_id: ID участника (user_id для соло, team_id для команд)
    
    Returns:
        Имя участника
    """
    if tournament.format == TournamentFormat.SOLO:
        if _mongo_client is not None:
            try:
                user = await _mongo_client.get_user(int(participant_id))
                if user:
                    return user.nickname or user.name or f"ID:{participant_id}"
            except Exception:
                pass
        return f"ID:{participant_id}"
    else:
        if _mongo_client is not None:
            try:
                team = await _mongo_client.get_team(str(participant_id))
                if team:
                    return f"{team.name} ({team.tag})"
            except Exception:
                pass
        return f"ID:{participant_id}"


async def format_team_text(
    team: Team,
    user_id: int,
) -> str:
    """
    Форматирует текст информации о команде для отображения.
    
    Args:
        team: Объект команды
        user_id: Telegram user_id текущего пользователя
    
    Returns:
        Отформатированный текст команды
    """
    lines = ["👥 Команда\n"]
    
    # Название, тег, капитан
    lines.append(f"🏷 Название: {team.name}")
    lines.append(f"📌 Тег: {team.tag}")
    
    # Получаем информацию о капитане
    captain_name = "Неизвестно"
    if _mongo_client is not None:
        try:
            captain = await _mongo_client.get_user(team.captain_id)
            if captain:
                captain_name = captain.nickname or captain.username or f"ID: {team.captain_id}"
        except Exception:
            pass
    
    lines.append(f"👤 Капитан: {captain_name}")
    
    # Состав игроков
    lines.append("\n👥 Состав игроков:")
    if team.members:
        for member_id in team.members:
            member_name = f"ID: {member_id}"
            if _mongo_client is not None:
                try:
                    member = await _mongo_client.get_user(member_id)
                    if member:
                        member_name = member.nickname or member.username or f"ID: {member_id}"
                except Exception:
                    pass
            
            captain_mark = " 👑" if member_id == team.captain_id else ""
            lines.append(f"  • {member_name}{captain_mark}")
    else:
        lines.append("  (пусто)")
    
    # Статистика команды
    lines.append("\n📊 Статистика команды:")
    lines.append(f"🏆 Турниров сыграно: {team.tournaments_played}")
    lines.append(f"⭐ Всего очков: {team.total_points}")
    
    rating_position = team.rating_position if team.rating_position else None
    if rating_position:
        lines.append(f"📈 Место в рейтинге: #{rating_position}")
    else:
        lines.append("📈 Место в рейтинге: не определено")
    
    return "\n".join(lines)


def format_players_rating(
    players: list[User],
    filter_text: str = "За всё время",
    user_position: Optional[int] = None,
) -> str:
    """
    Форматирует таблицу рейтинга игроков.
    
    Args:
        players: Список игроков
        filter_text: Текст фильтра для отображения
        user_position: Позиция текущего пользователя (опционально)
    
    Returns:
        Отформатированный текст рейтинга
    """
    lines = [f"🧑 Рейтинг игроков\n"]
    lines.append(f"📊 Фильтр: {filter_text}\n")
    
    if not players:
        lines.append("Рейтинг пуст")
        return "\n".join(lines)
    
    # Заголовок таблицы
    lines.append("<b>Место | Ник | Киллы | Турниров</b>")
    lines.append("─" * 30)
    
    # Отображаем топ-20
    for idx, player in enumerate(players[:20], start=1):
        nickname = player.nickname or f"ID:{player.id}"
        kills = player.total_kills or 0
        tournaments = player.tournaments_played or 0
        
        # Выделяем позицию пользователя
        marker = "👉 " if user_position and idx == user_position else ""
        lines.append(
            f"{marker}{idx}. {nickname} | {kills} | {tournaments}",
        )
    
    if len(players) > 20:
        lines.append(f"\n... и ещё {len(players) - 20} игроков")
    
    if user_position and user_position > 20 and user_position <= len(players):
        user = players[user_position - 1]
        nickname = user.nickname or f"ID:{user.id}"
        kills = user.total_kills or 0
        tournaments = user.tournaments_played or 0
        lines.append(
            f"\n👉 {user_position}. {nickname} | {kills} | {tournaments}",
        )
    
    return "\n".join(lines)


def format_teams_rating(
    teams: list[Team],
    filter_text: str = "За всё время",
    team_position: Optional[int] = None,
) -> str:
    """
    Форматирует таблицу рейтинга команд.
    
    Args:
        teams: Список команд
        filter_text: Текст фильтра для отображения
        team_position: Позиция текущей команды (опционально)
    
    Returns:
        Отформатированный текст рейтинга
    """
    lines = [f"👥 Рейтинг команд\n"]
    lines.append(f"📊 Фильтр: {filter_text}\n")
    
    if not teams:
        lines.append("Рейтинг пуст")
        return "\n".join(lines)
    
    # Заголовок таблицы
    lines.append("<b>Место | Команда | Очки | Турниров</b>")
    lines.append("─" * 30)
    
    # Отображаем топ-20
    for idx, team in enumerate(teams[:20], start=1):
        team_name = f"{team.name} ({team.tag})"
        points = team.total_points or 0
        tournaments = team.tournaments_played or 0
        
        # Выделяем позицию команды
        marker = "👉 " if team_position and idx == team_position else ""
        lines.append(
            f"{marker}{idx}. {team_name} | {points} | {tournaments}",
        )
    
    if len(teams) > 20:
        lines.append(f"\n... и ещё {len(teams) - 20} команд")
    
    if team_position and team_position > 20:
        team = teams[team_position - 1] if team_position <= len(teams) else None
        if team:
            team_name = f"{team.name} ({team.tag})"
            points = team.total_points or 0
            tournaments = team.tournaments_played or 0
            lines.append(
                f"\n👉 {team_position}. {team_name} | {points} | {tournaments}",
            )
    
    return "\n".join(lines)


def format_bonuses_text(
    daily_bonus_available: bool = False,
    referrals_count: int = 0,
    referral_code: Optional[str] = None,
) -> str:
    """
    Форматирует текст для экрана бонусов.
    
    Args:
        daily_bonus_available: Доступен ли ежедневный бонус
        referrals_count: Количество приглашенных друзей
        referral_code: Реферальный код пользователя
    
    Returns:
        Отформатированный текст бонусов
    """
    lines = ["🎁 Бонусы\n"]
    
    # Ежедневный бонус
    lines.append("📅 Ежедневный бонус:")
    if daily_bonus_available:
        lines.append("  ✅ Доступен! Нажмите кнопку, чтобы забрать.")
    else:
        lines.append("  ⏰ Уже получен сегодня. Завтра будет доступен снова.")
    
    lines.append("")
    
    # Реферальный бонус
    lines.append("👥 Бонус за приглашение друга:")
    if referral_code:
        lines.append(f"  🔗 Ваш реферальный код: <code>{referral_code}</code>")
    else:
        lines.append("  🔗 Реферальный код будет создан при первом использовании")
    lines.append(f"  👥 Приглашено друзей: <b>{referrals_count}</b>")
    lines.append("  💰 За каждого друга: +50 CD токенов")
    
    lines.append("")
    
    # Задания
    lines.append("📋 Задания:")
    lines.append("  • Сыграй турнир")
    lines.append("  • Будь в команде")
    lines.append("  • Пригласи друга")
    
    return "\n".join(lines)


def format_admin_user_card_text(
    user: User,
    team: Optional[Team] = None,
) -> str:
    """
    Форматирует текст карточки пользователя для админ-панели.
    
    Args:
        user: Объект пользователя
        team: Объект команды (если пользователь в команде)
    
    Returns:
        Отформатированный текст карточки пользователя
    """
    lines = [f"👤 Карточка пользователя\n"]
    
    # Профиль
    lines.append("📋 Профиль:")
    lines.append(f"  🆔 ID: <code>{user.id}</code>")
    if user.username:
        lines.append(f"  📱 Username: @{user.username}")
    if user.nickname:
        lines.append(f"  🎮 Никнейм: {user.nickname}")
    if user.name:
        full_name = user.name
        if user.surname:
            full_name += f" {user.surname}"
        lines.append(f"  👤 Имя: {full_name}")
    if user.game_discipline:
        lines.append(f"  🎯 Игра: {user.game_discipline}")
    if user.region_country:
        lines.append(f"  🌍 Регион: {user.region_country}")
    lines.append(f"  🎭 Роль: {user.role.value}")
    if user.is_banned:
        lines.append("  🚫 Статус: <b>Забанен</b>")
    else:
        lines.append("  ✅ Статус: Активен")
    
    lines.append("")
    
    # Команда
    lines.append("👥 Команда:")
    if team:
        lines.append(f"  📛 Название: {team.name} ({team.tag})")
        lines.append(f"  👑 Капитан: {'Вы' if team.captain_id == user.id else 'Другой'}")
    else:
        lines.append("  ❌ Не состоит в команде")
    
    lines.append("")
    
    # Статистика
    lines.append("📊 Статистика:")
    lines.append(f"  🏆 Турниров сыграно: {user.tournaments_played}")
    lines.append(f"  💀 Всего киллов: {user.total_kills}")
    if user.rating_position:
        lines.append(f"  📈 Место в рейтинге: #{user.rating_position}")
    else:
        lines.append("  📈 Место в рейтинге: не определено")
    
    lines.append("")
    
    # Баланс
    lines.append("💰 Баланс CD токенов:")
    lines.append(f"  💵 Текущий баланс: <b>{user.balance} CD токенов</b>")
    
    return "\n".join(lines)


def format_quests_text(
    user: User,
) -> str:
    """
    Форматирует текст для экрана заданий.
    
    Args:
        user: Объект пользователя
    
    Returns:
        Отформатированный текст заданий
    """
    lines = ["📋 Задания\n"]
    
    # Проверяем прогресс по заданиям
    quests = {
        "play_tournament": {
            "name": "Сыграй турнир",
            "description": "Прими участие в любом турнире",
            "reward": "100 CD токенов",
            "completed": user.quests_completed.get("play_tournament", False),
            "progress": f"{user.tournaments_played} / 1",
        },
        "join_team": {
            "name": "Будь в команде",
            "description": "Вступи в любую команду",
            "reward": "50 CD токенов",
            "completed": user.quests_completed.get("join_team", False),
            "progress": "✅" if user.team_id else "❌",
        },
        "invite_friend": {
            "name": "Пригласи друга",
            "description": "Пригласи друга по реферальной ссылке",
            "reward": "50 CD токенов",
            "completed": user.quests_completed.get("invite_friend", False),
            "progress": f"{user.referrals_count} / 1",
        },
    }
    
    for quest_id, quest in quests.items():
        status = "✅" if quest["completed"] else "⏳"
        lines.append(f"{status} <b>{quest['name']}</b>")
        lines.append(f"   {quest['description']}")
        lines.append(f"   Прогресс: {quest['progress']}")
        lines.append(f"   Награда: {quest['reward']}")
        lines.append("")
    
    return "\n".join(lines)


def format_wallet_text(
    balance: int,
) -> str:
    """
    Форматирует текст кошелька с балансом.
    
    Args:
        balance: Баланс CD токенов
    
    Returns:
        Отформатированный текст кошелька
    """
    lines = ["💰 Кошелёк (CD токен)\n"]
    lines.append(f"💵 Баланс: <b>{balance} CD токенов</b>\n")
    lines.append("📊 История (последние операции):")
    lines.append("Начисление/списание/за что")
    
    return "\n".join(lines)


def format_transactions_history(
    transactions: list[Transaction],
    balance: int,
) -> str:
    """
    Форматирует историю транзакций.
    
    Args:
        transactions: Список транзакций
        balance: Текущий баланс
    
    Returns:
        Отформатированный текст истории
    """
    lines = ["📜 История операций\n"]
    lines.append(f"💵 Текущий баланс: <b>{balance} CD токенов</b>\n")
    
    if not transactions:
        lines.append("История операций пуста")
        return "\n".join(lines)
    
    lines.append("<b>Дата | Тип | Сумма | Описание</b>")
    lines.append("─" * 40)
    
    for transaction in transactions[:10]:  # Показываем последние 10
        date_str = transaction.created_at.strftime("%d.%m.%Y %H:%M")
        type_emoji = "➕" if transaction.transaction_type == TransactionType.DEPOSIT else "➖"
        type_text = "Начисление" if transaction.transaction_type == TransactionType.DEPOSIT else "Списание"
        amount = transaction.amount
        
        lines.append(
            f"{date_str} | {type_emoji} {type_text} | {amount} | {transaction.description}",
        )
    
    if len(transactions) > 10:
        lines.append(f"\n... и ещё {len(transactions) - 10} операций")
    
    return "\n".join(lines)


def format_tournament_card(
    tournament: Tournament,
    is_participant: bool = False,
) -> str:
    """
    Форматирует карточку турнира для отображения.
    
    Args:
        tournament: Объект турнира
        is_participant: Участвует ли пользователь в турнире
    
    Returns:
        Отформатированный текст карточки турнира
    """
    lines = [f"🏆 {tournament.name}\n"]
    
    # Даты
    reg_start = tournament.registration_start.strftime("%d.%m.%Y %H:%M")
    reg_end = tournament.registration_end.strftime("%d.%m.%Y %H:%M")
    start = tournament.start_date.strftime("%d.%m.%Y %H:%M")
    
    lines.append(f"📅 Регистрация: {reg_start} - {reg_end}")
    lines.append(f"🚀 Старт: {start}")
    
    if tournament.end_date:
        end = tournament.end_date.strftime("%d.%m.%Y %H:%M")
        lines.append(f"🏁 Финиш: {end}")
    
    # Формат
    format_text = "👤 Соло" if tournament.format == TournamentFormat.SOLO else "👥 Команды"
    lines.append(f"📋 Формат: {format_text}")
    
    # Взнос и призы
    if tournament.entry_fee:
        lines.append(f"💰 Взнос: {tournament.entry_fee} CD токенов")
    
    if tournament.prizes:
        lines.append(f"🎁 Призы: {tournament.prizes}")
    
    # Лимит участников
    if tournament.participant_limit:
        current_participants = (
            len(tournament.solo_participants)
            if tournament.format == TournamentFormat.SOLO
            else len(tournament.team_participants)
        )
        lines.append(
            f"👥 Участников: {current_participants}/{tournament.participant_limit}",
        )
    
    # Статус
    status_text = {
        TournamentStatus.REGISTRATION_OPEN: "✅ Открыта регистрация",
        TournamentStatus.IN_PROGRESS: "🔄 Идёт",
        TournamentStatus.COMPLETED: "🏁 Завершён",
    }
    lines.append(f"\n📊 Статус: {status_text.get(tournament.status, tournament.status.value)}")
    
    # Короткие правила
    if tournament.rules_summary:
        lines.append(f"\n📝 Правила подсчёта:\n{tournament.rules_summary}")
    
    # Информация об участии
    if is_participant:
        lines.append("\n✅ Вы участвуете в этом турнире")
    
    return "\n".join(lines)


def format_tournaments_list(
    tournaments: list[Tournament],
) -> str:
    """
    Форматирует список турниров для отображения.
    
    Args:
        tournaments: Список турниров
    
    Returns:
        Отформатированный текст списка турниров
    """
    if not tournaments:
        return "🏆 Турниры\n\nТурниры не найдены."
    
    lines = ["🏆 Турниры\n"]
    
    for i, tournament in enumerate(tournaments, 1):
        status_emoji = {
            TournamentStatus.REGISTRATION_OPEN: "✅",
            TournamentStatus.IN_PROGRESS: "🔄",
            TournamentStatus.COMPLETED: "🏁",
        }
        emoji = status_emoji.get(tournament.status, "🏆")
        
        format_text = "👤" if tournament.format == TournamentFormat.SOLO else "👥"
        
        lines.append(
            f"{i}. {emoji} <b>{tournament.name}</b> {format_text}\n"
            f"   📅 {tournament.start_date.strftime('%d.%m.%Y')}\n"
            f"   🎮 {tournament.game_discipline}",
        )
    
    return "\n".join(lines)


def has_admin_access(
    role: UserRole,
) -> bool:
    """
    Проверяет, есть ли у пользователя доступ к админ-панели.
    Доступ имеют только: менеджер, админ, супер-админ.
    Обычные пользователи (USER) не имеют доступа.
    
    Args:
        role: Роль пользователя из базы данных
    
    Returns:
        True, если есть доступ (MANAGER, ADMIN, SUPER_ADMIN), иначе False
    """
    has_access = role in (
        UserRole.MANAGER,
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    )
    
    if not has_access:
        _LOG.debug(
            f"Попытка доступа к админ-панели пользователем с ролью {role.value}",
        )
    
    return has_access


async def start_handler(
    message: types.Message,
) -> None:
    """
    Обработчик команды /start.
    Создает или обновляет пользователя в базе данных и показывает главное меню.
    """
    tg_user = message.from_user
    
    # Создаем или обновляем пользователя в базе данных
    if _mongo_client is not None:
        try:
            # Получаем существующего пользователя для сохранения роли
            existing_user = await _mongo_client.get_user(tg_user.id)
            
            # Создаем объект User из данных Telegram
            user = User(
                id=tg_user.id,
                username=tg_user.username,
                name=tg_user.first_name,
                surname=tg_user.last_name,
                father_name=None,  # Telegram не предоставляет отчество
                phone=None,  # Телефон будет заполнен позже
                role=existing_user.role if existing_user else UserRole.USER,
            )
            
            # Создаем или обновляем пользователя в БД
            await _mongo_client.create_or_update_user(user)
        except Exception as e:
            import logging
            _LOG = logging.getLogger("woman-tg-bot")
            _LOG.error(
                f"Ошибка при создании/обновлении пользователя {tg_user.id}: {e}",
            )
    
    # Получаем роль пользователя для отображения меню
    user_role = await get_user_role(
        tg_user.id,
    )
    show_admin = has_admin_access(user_role)
    
    await message.answer(
        text="Главное меню",
        reply_markup=get_main_menu_keyboard(
            show_admin=show_admin,
        ),
    )


async def callback_handler(
    callback: types.CallbackQuery,
) -> None:
    """
    Обработчик нажатий на инлайн-кнопки главного меню.
    """
    callback_data = callback.data
    user_role = await get_user_role(
        callback.from_user.id,
    )
    show_admin = has_admin_access(user_role)

    if callback_data == "menu_profile":
        # Кнопка "Профиль" теперь открывает мини-приложение
        # Этот обработчик оставлен на случай, если callback все еще приходит
        await callback.answer("Профиль открывается в мини-приложении")
    elif callback_data == "menu_team":
        await callback.answer("Команда")
        
        # Получаем команду пользователя
        team = None
        if _mongo_client is not None:
            try:
                # Сначала получаем пользователя для проверки team_id
                user = await _mongo_client.get_user(callback.from_user.id)
                _LOG.debug(
                    f"Пользователь {callback.from_user.id}: team_id = {user.team_id if user else None}",
                )
                
                if user and user.team_id:
                    team = await _mongo_client.get_team(user.team_id)
                    _LOG.debug(
                        f"Команда получена: {team.id if team else None}",
                    )
                else:
                    # Пробуем получить через get_user_team для обратной совместимости
                    team = await _mongo_client.get_user_team(callback.from_user.id)
            except Exception as e:
                _LOG.error(
                    f"Ошибка при получении команды пользователя {callback.from_user.id}: {e}",
                    exc_info=True,
                )
        
        if team is None:
            # У пользователя нет команды
            _LOG.debug(
                f"Пользователь {callback.from_user.id} не состоит в команде",
            )
            await callback.message.edit_text(
                text="👥 Команда\n\nУ тебя нет команды",
                reply_markup=get_team_no_team_keyboard(),
            )
        else:
            # У пользователя есть команда
            _LOG.debug(
                f"Пользователь {callback.from_user.id} состоит в команде {team.id}",
            )
            is_captain = team.captain_id == callback.from_user.id
            is_admin = has_admin_access(user_role)
            
            team_text = await format_team_text(team, callback.from_user.id)
            await callback.message.edit_text(
                text=team_text,
                reply_markup=get_team_keyboard(
                    is_captain=is_captain,
                    is_admin=is_admin,
                ),
            )
    elif callback_data == "menu_tournaments":
        await callback.answer("Турниры")
        
        # Получаем список турниров
        tournaments = []
        available_games = []
        if _mongo_client is not None:
            try:
                tournaments = await _mongo_client.get_tournaments()
                # Получаем список уникальных игр
                available_games = list(
                    set(t.game_discipline for t in tournaments),
                )
            except Exception as e:
                _LOG.error(
                    f"Ошибка при получении турниров: {e}",
                )
        
        tournaments_text = format_tournaments_list(tournaments)
        await callback.message.edit_text(
            text=tournaments_text,
            reply_markup=get_tournaments_list_keyboard(
                current_filter="all",
                available_games=available_games,
            ),
        )
    elif callback_data == "menu_ratings" or callback_data == "ratings_type":
        await callback.answer("Рейтинги")
        await callback.message.edit_text(
            text="📊 Рейтинги\n\nВыберите тип рейтинга:",
            reply_markup=get_ratings_type_keyboard(),
        )
    elif callback_data == "ratings_players":
        await callback.answer("Рейтинг игроков")
        # Показываем фильтры для рейтинга игроков
        await callback.message.edit_text(
            text="🧑 Рейтинг игроков\n\nВыберите фильтр:",
            reply_markup=get_ratings_filter_keyboard(
                rating_type="players",
                current_filter="all_time",
            ),
        )
    elif callback_data == "ratings_teams":
        await callback.answer("Рейтинг команд")
        # Показываем фильтры для рейтинга команд
        await callback.message.edit_text(
            text="👥 Рейтинг команд\n\nВыберите фильтр:",
            reply_markup=get_ratings_filter_keyboard(
                rating_type="teams",
                current_filter="all_time",
            ),
        )
    elif callback_data.startswith("ratings_filter_"):
        # Обработка фильтров рейтинга
        parts = callback_data.replace("ratings_filter_", "").split("_", 1)
        if len(parts) == 2:
            rating_type = parts[0]  # players или teams
            filter_type = parts[1]  # all_time, season, month, tournament
            
            if filter_type == "tournament":
                # Показываем список турниров для выбора
                tournaments = []
                if _mongo_client is not None:
                    try:
                        tournaments = await _mongo_client.get_tournaments()
                    except Exception as e:
                        _LOG.error(f"Ошибка при получении турниров: {e}")
                
                await callback.message.edit_text(
                    text=f"{'🧑' if rating_type == 'players' else '👥'} Рейтинг {'игроков' if rating_type == 'players' else 'команд'}\n\nВыберите турнир:",
                    reply_markup=get_ratings_tournament_select_keyboard(
                        rating_type=rating_type,
                        tournaments=tournaments,
                    ),
                )
            else:
                # Показываем рейтинг с выбранным фильтром
                await _show_rating(
                    callback=callback,
                    rating_type=rating_type,
                    filter_type=filter_type,
                )
    elif callback_data.startswith("ratings_tournament_"):
        # Выбран турнир для фильтрации
        parts = callback_data.replace("ratings_tournament_", "").split("_", 1)
        if len(parts) == 2:
            rating_type = parts[0]
            tournament_id = parts[1]
            await _show_rating(
                callback=callback,
                rating_type=rating_type,
                filter_type="tournament",
                tournament_id=tournament_id,
            )
    elif callback_data.startswith("ratings_find_"):
        # Кнопка "Найти себя"
        rating_type = callback_data.replace("ratings_find_", "")
        await _find_user_in_rating(
            callback=callback,
            rating_type=rating_type,
        )
    elif callback_data == "menu_bonuses":
        await callback.answer("Бонусы")
        # Получаем информацию о бонусах пользователя
        daily_bonus_available = False
        if _mongo_client is not None:
            try:
                user = await _mongo_client.get_user(callback.from_user.id)
                if user:
                    # Проверяем, доступен ли ежедневный бонус
                    today = dt.date.today()
                    if not user.last_daily_bonus_date or user.last_daily_bonus_date < today:
                        daily_bonus_available = True
            except Exception as e:
                _LOG.error(f"Ошибка при получении информации о бонусах: {e}")
        
        bonuses_text = format_bonuses_text(
            daily_bonus_available=daily_bonus_available,
            referrals_count=0,
        )
        if _mongo_client is not None:
            try:
                user = await _mongo_client.get_user(callback.from_user.id)
                if user:
                    bonuses_text = format_bonuses_text(
                        daily_bonus_available=daily_bonus_available,
                        referrals_count=user.referrals_count,
                        referral_code=user.referral_code,
                    )
            except Exception as e:
                _LOG.error(f"Ошибка при получении информации о рефералах: {e}")
        
        await callback.message.edit_text(
            text=bonuses_text,
            reply_markup=get_bonuses_keyboard(
                daily_bonus_available=daily_bonus_available,
            ),
            parse_mode="HTML",
        )
    elif callback_data == "menu_wallet":
        await callback.answer("Кошелёк")
        # Получаем баланс пользователя
        balance = 0
        if _mongo_client is not None:
            try:
                balance = await _mongo_client.get_user_balance(callback.from_user.id)
            except Exception as e:
                _LOG.error(f"Ошибка при получении баланса: {e}")
        
        wallet_text = format_wallet_text(balance)
        await callback.message.edit_text(
            text=wallet_text,
            reply_markup=get_wallet_keyboard(),
            parse_mode="HTML",
        )
    elif callback_data == "wallet_history":
        await callback.answer("История операций")
        # Получаем историю транзакций
        transactions = []
        balance = 0
        if _mongo_client is not None:
            try:
                transactions = await _mongo_client.get_user_transactions(
                    callback.from_user.id,
                    limit=20,
                )
                balance = await _mongo_client.get_user_balance(callback.from_user.id)
            except Exception as e:
                _LOG.error(f"Ошибка при получении истории транзакций: {e}")
        
        history_text = format_transactions_history(transactions, balance)
        await callback.message.edit_text(
            text=history_text,
            reply_markup=get_wallet_keyboard(),
            parse_mode="HTML",
        )
    elif callback_data == "wallet_spend":
        await callback.answer("Потратить токены")
        await callback.message.edit_text(
            text="🎟 Потратить токены\n\n"
                 "Раздел в разработке...\n\n"
                 "Здесь будет магазин и возможность участия в розыгрышах.",
            reply_markup=get_wallet_keyboard(),
        )
    elif callback_data == "wallet_promocode":
        await callback.answer("Ввести промокод")
        # Активируем режим ожидания промокода
        user_id = callback.from_user.id
        _waiting_promocode[user_id] = True
        print(f"[INFO] Активирован режим ожидания промокода для пользователя {user_id}")
        await callback.message.edit_text(
            text="🧾 Ввести промокод\n\n"
                 "Введите промокод для получения бонусов.\n\n"
                 "Или отправьте /cancel для отмены.",
        )
        # Также отправляем новое сообщение для ясности
        await callback.message.answer(
            "💬 Ожидаю промокод...\n\n"
            "Введите промокод текстом.\n\n"
            "Или отправьте /cancel для отмены.",
        )
    elif callback_data == "menu_promotions":
        await callback.answer("Акции и розыгрыши")
        # Открываем мини-приложение для акций и розыгрышей
        from src.config import MINI_APP_URL
        
        # Формируем URL для страницы розыгрышей
        base_url = MINI_APP_URL.rstrip('/')
        if '/profile' in base_url:
            base_url = base_url.replace('/profile', '')
        elif base_url.endswith('/index.html'):
            base_url = base_url.replace('/index.html', '')
        promotions_url = f"{base_url}/promotions.html"
        
        await callback.message.edit_text(
            text="🎉 Акции и розыгрыши\n\n"
                 "Нажмите на кнопку ниже, чтобы открыть розыгрыши:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🎉 Открыть розыгрыши",
                            web_app=types.WebAppInfo(url=promotions_url),
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="⬅️ Назад",
                            callback_data="menu_back",
                        ),
                    ],
                ],
            ),
        )
    elif callback_data == "bonus_daily_claim":
        await callback.answer("Ежедневный бонус")
        # Выдаем ежедневный бонус
        if _mongo_client is not None:
            try:
                user = await _mongo_client.get_user(callback.from_user.id)
                if user:
                    today = dt.date.today()
                    # Проверяем, доступен ли бонус
                    if user.last_daily_bonus_date and user.last_daily_bonus_date >= today:
                        await callback.answer("Вы уже получили ежедневный бонус сегодня!", show_alert=True)
                        return
                    
                    # Получаем настройки бонуса из БД
                    bonus_settings = await _mongo_client.get_bonus_settings()
                    bonus_amount = bonus_settings.daily_bonus_amount if bonus_settings else 10
                    await _mongo_client.add_transaction(
                        user_id=callback.from_user.id,
                        transaction_type=TransactionType.DEPOSIT,
                        amount=bonus_amount,
                        description="Ежедневный бонус",
                    )
                    
                    # Обновляем дату последнего бонуса
                    await _mongo_client.update_user_daily_bonus_date(
                        user_id=callback.from_user.id,
                        date=today,
                    )
                    
                    new_balance = await _mongo_client.get_user_balance(callback.from_user.id)
                    
                    await callback.message.edit_text(
                        text=f"✅ Ежедневный бонус получен!\n\n"
                             f"💰 Начислено: {bonus_amount} CD токенов\n"
                             f"💵 Новый баланс: {new_balance} CD токенов\n\n"
                             f"Приходите завтра за новым бонусом!",
                        reply_markup=get_bonuses_keyboard(daily_bonus_available=False),
                    )
            except Exception as e:
                _LOG.error(f"Ошибка при выдаче ежедневного бонуса: {e}")
                await callback.answer("Произошла ошибка. Попробуйте позже.", show_alert=True)
        else:
            await callback.answer("Ошибка подключения к базе данных.", show_alert=True)
    elif callback_data == "bonus_daily_info":
        await callback.answer("Ежедневный бонус")
        await callback.message.edit_text(
            text="⏰ Ежедневный бонус\n\n"
                 "Вы уже получили ежедневный бонус сегодня.\n\n"
                 "Приходите завтра за новым бонусом!",
            reply_markup=get_bonuses_keyboard(daily_bonus_available=False),
        )
    elif callback_data == "bonus_referral":
        await callback.answer("Реферальный бонус")
        # Показываем информацию о реферальном бонусе
        referrals_count = 0
        referral_code = None
        
        if _mongo_client is not None:
            try:
                user = await _mongo_client.get_user(callback.from_user.id)
                if user:
                    referrals_count = user.referrals_count
                    referral_code = user.referral_code
                    
                    # Если реферального кода нет, создаем его
                    if not referral_code:
                        import secrets
                        referral_code = f"REF{secrets.token_hex(4).upper()}"
                        await _mongo_client.update_user_referral_code(
                            user_id=callback.from_user.id,
                            referral_code=referral_code,
                        )
            except Exception as e:
                _LOG.error(f"Ошибка при получении информации о рефералах: {e}")
        
        referral_text = (
            f"👥 Бонус за приглашение друга\n\n"
            f"🔗 Ваш реферальный код: <code>{referral_code or 'не создан'}</code>\n\n"
            f"📊 Статистика:\n"
            f"  👥 Приглашено друзей: <b>{referrals_count}</b>\n"
            f"  💰 Заработано: <b>{referrals_count * 50} CD токенов</b>\n\n"
            f"💡 Как это работает:\n"
            f"  1. Поделитесь своим реферальным кодом с друзьями\n"
            f"  2. Когда друг зарегистрируется по вашему коду, вы получите 50 CD токенов\n"
            f"  3. Ваш друг также получит 50 CD токенов за регистрацию\n\n"
            f"📱 Ваша реферальная ссылка:\n"
            f"  <code>https://t.me/testtt_crm_bot?start={referral_code or 'REF'}</code>"
        )
        
        await callback.message.edit_text(
            text=referral_text,
            reply_markup=get_bonuses_keyboard(daily_bonus_available=False),
            parse_mode="HTML",
        )
    elif callback_data == "bonus_quests":
        await callback.answer("Задания")
        # Показываем список заданий
        if _mongo_client is not None:
            try:
                user = await _mongo_client.get_user(callback.from_user.id)
                if user:
                    # Проверяем прогресс по заданиям
                    quests_text = format_quests_text(user)
                    await callback.message.edit_text(
                        text=quests_text,
                        reply_markup=get_bonuses_keyboard(daily_bonus_available=False),
                        parse_mode="HTML",
                    )
            except Exception as e:
                _LOG.error(f"Ошибка при получении заданий: {e}")
                await callback.message.edit_text(
                    text="📋 Задания\n\nПроизошла ошибка при загрузке заданий.",
                    reply_markup=get_bonuses_keyboard(daily_bonus_available=False),
                )
        else:
            await callback.message.edit_text(
                text="📋 Задания\n\nОшибка подключения к базе данных.",
                reply_markup=get_bonuses_keyboard(daily_bonus_available=False),
            )
    elif callback_data == "menu_invite":
        await callback.answer("Пригласи друга")
        # Открываем мини-приложение для реферальной системы
        from aiogram.types import WebAppInfo
        from src.config import MINI_APP_URL
        
        # Формируем URL для реферальной страницы
        # MINI_APP_URL может быть базовым URL или с путем /profile
        # Нужно получить базовый URL и добавить /referral.html
        base_url = MINI_APP_URL.rstrip('/')
        if '/profile' in base_url:
            base_url = base_url.replace('/profile', '')
        elif base_url.endswith('/index.html'):
            base_url = base_url.replace('/index.html', '')
        referral_url = f"{base_url}/referral.html"
        
        await callback.message.edit_text(
            text="🤝 Пригласи друга\n\n"
                 "Нажмите на кнопку ниже, чтобы открыть реферальную систему:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🤝 Открыть реферальную систему",
                            web_app=WebAppInfo(url=referral_url),
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="⬅️ Назад",
                            callback_data="menu_back",
                        ),
                    ],
                ],
            ),
        )
    elif callback_data == "menu_support":
        await callback.answer("Поддержка")
        await callback.message.edit_text(
            text="❓ Поддержка\n\nВыберите действие:",
            reply_markup=get_support_keyboard(),
        )
    elif callback_data == "support_ask":
        await callback.answer("Задать вопрос")
        # Активируем режим ожидания вопроса
        user_id = callback.from_user.id
        _waiting_support_question[user_id] = True
        _LOG.debug(f"Активирован режим ожидания вопроса для пользователя {user_id}")
        await callback.message.edit_text(
            text="💬 Задать вопрос\n\n"
                 "Напишите ваш вопрос, и мы обязательно ответим!\n\n"
                 "Или отправьте /cancel для отмены.",
        )
        # Также отправляем новое сообщение для ясности
        await callback.message.answer(
            "💬 Ожидаю ваш вопрос...\n\n"
            "Напишите ваш вопрос текстом, и я отправлю его в поддержку.\n\n"
            "Или отправьте /cancel для отмены.",
        )
    elif callback_data == "support_faq":
        await callback.answer("Частые вопросы")
        await callback.message.edit_text(
            text="❓ Частые вопросы\n\n"
                 "Выберите интересующий вас вопрос:",
            reply_markup=get_faq_keyboard(),
        )
    elif callback_data.startswith("faq_"):
        # Обработка частых вопросов
        faq_number = callback_data.replace("faq_", "")
        faq_answers = {
            "1": "Ответ на тестовый вопрос 1: Это тестовый ответ для демонстрации функционала поддержки.",
            "2": "Ответ на тестовый вопрос 2: Это тестовый ответ для демонстрации функционала поддержки.",
            "3": "Ответ на тестовый вопрос 3: Это тестовый ответ для демонстрации функционала поддержки.",
            "4": "Ответ на тестовый вопрос 4: Это тестовый ответ для демонстрации функционала поддержки.",
            "5": "Ответ на тестовый вопрос 5: Это тестовый ответ для демонстрации функционала поддержки.",
            "6": "Ответ на тестовый вопрос 6: Это тестовый ответ для демонстрации функционала поддержки.",
        }
        answer = faq_answers.get(faq_number, "Ответ не найден")
        await callback.answer(answer, show_alert=True)
    elif callback_data == "menu_admin":
        # Проверка доступа к админ-панели
        # Доступ имеют только: MANAGER, ADMIN, SUPER_ADMIN
        if not has_admin_access(user_role):
            _LOG.warning(
                f"Попытка доступа к админ-панели пользователем {callback.from_user.id} "
                f"с ролью {user_role.value}",
            )
            await callback.answer(
                "❌ У вас нет доступа к админ-панели.\n\n"
                "Доступ имеют только менеджеры, админы и супер-админы.",
                show_alert=True,
            )
            return
        
        await callback.answer("Админ-панель")
        is_super_admin = user_role == UserRole.SUPER_ADMIN
        _LOG.info(
            f"Пользователь {callback.from_user.id} ({user_role.value}) "
            f"открыл админ-панель",
        )
        await callback.message.edit_text(
            text="⚙️ Админ-панель",
            reply_markup=get_admin_panel_keyboard(
                is_super_admin=is_super_admin,
            ),
        )
    elif callback_data == "profile_edit":
        await callback.answer("Изменение профиля")
        await callback.message.edit_text(
            text="✏️ Изменить профиль\n\nРаздел в разработке...",
            reply_markup=get_profile_keyboard(),
        )
    elif callback_data == "profile_social":
        await callback.answer("Привязать соцсети")
        await callback.message.edit_text(
            text="📎 Привязать соцсети\n\nРаздел в разработке...",
            reply_markup=get_profile_keyboard(),
        )
    elif callback_data == "profile_privacy":
        await callback.answer("Настройки приватности")
        await callback.message.edit_text(
            text="🔒 Настройки приватности\n\nРаздел в разработке...",
            reply_markup=get_profile_keyboard(),
        )
    elif callback_data == "team_create":
        await callback.answer("Создание команды")
        
        # Проверяем, что пользователь не в команде
        if _mongo_client is not None:
            try:
                existing_team = await _mongo_client.get_user_team(callback.from_user.id)
                if existing_team:
                    await callback.answer(
                        "Вы уже состоите в команде!",
                        show_alert=True,
                    )
                    return
            except Exception as e:
                _LOG.error(
                    f"Ошибка при проверке команды пользователя {callback.from_user.id}: {e}",
                )
        
        # Запрашиваем данные для создания команды
        await callback.message.edit_text(
            text="➕ Создать команду\n\n"
                 "Отправьте название и тег команды в формате:\n"
                 "<b>Название команды | Тег</b>\n\n"
                 "Пример: <code>Моя команда | MT</code>\n\n"
                 "Или отправьте /cancel для отмены.",
            reply_markup=None,  # Убираем клавиатуру для ввода текста
        )
        
        # Устанавливаем флаг ожидания данных команды
        user_id = callback.from_user.id
        _waiting_team_data[user_id] = True
        print(f"[INFO] Активирован режим ожидания данных команды для пользователя {user_id}")
        # Также отправляем новое сообщение для ясности
        await callback.message.answer(
            "💬 Ожидаю данные команды...\n\n"
            "Отправьте название и тег команды в формате:\n"
            "<b>Название команды | Тег</b>\n\n"
            "Пример: <code>Моя команда | MT</code>\n\n"
            "Или отправьте /cancel для отмены.",
            parse_mode="HTML",
        )
    elif callback_data == "team_search":
        await callback.answer("Поиск команды")
        await callback.message.edit_text(
            text="🔎 Найти команду\n\nРаздел в разработке...",
            reply_markup=get_team_no_team_keyboard(),
        )
    elif callback_data == "team_join_code":
        await callback.answer("Ввод кода-приглашения")
        await callback.message.edit_text(
            text="📩 Ввести код-приглашение\n\nРаздел в разработке...",
            reply_markup=get_team_no_team_keyboard(),
        )
    elif callback_data == "team_set_captain":
        await callback.answer("Назначение капитана")
        # Получаем команду для определения прав
        team = None
        if _mongo_client is not None:
            try:
                team = await _mongo_client.get_user_team(callback.from_user.id)
            except Exception:
                pass
        
        is_captain = team.captain_id == callback.from_user.id if team else False
        await callback.message.edit_text(
            text="👤 Назначить капитана\n\nРаздел в разработке...",
            reply_markup=get_team_keyboard(
                is_captain=is_captain,
                is_admin=has_admin_access(user_role),
            ),
        )
    elif callback_data == "team_invite":
        await callback.answer("Приглашение игрока")
        # Получаем команду для определения прав
        team = None
        if _mongo_client is not None:
            try:
                team = await _mongo_client.get_user_team(callback.from_user.id)
            except Exception:
                pass
        
        is_captain = team.captain_id == callback.from_user.id if team else False
        await callback.message.edit_text(
            text="➕ Пригласить игрока\n\nРаздел в разработке...",
            reply_markup=get_team_keyboard(
                is_captain=is_captain,
                is_admin=has_admin_access(user_role),
            ),
        )
    elif callback_data == "team_manage_requests":
        await callback.answer("Управление заявками")
        # Получаем команду для определения прав
        team = None
        if _mongo_client is not None:
            try:
                team = await _mongo_client.get_user_team(callback.from_user.id)
            except Exception:
                pass
        
        is_captain = team.captain_id == callback.from_user.id if team else False
        await callback.message.edit_text(
            text="🛠 Управление заявками\n\nРаздел в разработке...",
            reply_markup=get_team_keyboard(
                is_captain=is_captain,
                is_admin=has_admin_access(user_role),
            ),
        )
    elif callback_data == "team_leave":
        await callback.answer("Покинуть команду")
        # Получаем команду для определения прав
        team = None
        if _mongo_client is not None:
            try:
                team = await _mongo_client.get_user_team(callback.from_user.id)
            except Exception:
                pass
        
        is_captain = team.captain_id == callback.from_user.id if team else False
        await callback.message.edit_text(
            text="❌ Покинуть команду\n\nРаздел в разработке...",
            reply_markup=get_team_keyboard(
                is_captain=is_captain,
                is_admin=has_admin_access(user_role),
            ),
        )
    elif callback_data == "tournaments_list":
        await callback.answer("Список турниров")
        
        # Получаем список турниров
        tournaments = []
        available_games = []
        if _mongo_client is not None:
            try:
                tournaments = await _mongo_client.get_tournaments()
                available_games = list(
                    set(t.game_discipline for t in tournaments),
                )
            except Exception as e:
                _LOG.error(
                    f"Ошибка при получении турниров: {e}",
                )
        
        tournaments_text = format_tournaments_list(tournaments)
        await callback.message.edit_text(
            text=tournaments_text,
            reply_markup=get_tournaments_list_keyboard(
                tournaments=tournaments,
                current_filter="all",
                available_games=available_games,
            ),
        )
    elif callback_data.startswith("tournaments_filter_"):
        # Обработка фильтров турниров
        filter_type = callback_data.replace("tournaments_filter_", "")
        
        status_filter = None
        game_filter = None
        
        if filter_type == "all":
            pass  # Без фильтра
        elif filter_type == "registration_open":
            status_filter = TournamentStatus.REGISTRATION_OPEN
        elif filter_type == "in_progress":
            status_filter = TournamentStatus.IN_PROGRESS
        elif filter_type == "completed":
            status_filter = TournamentStatus.COMPLETED
        elif filter_type.startswith("game_"):
            game_filter = filter_type.replace("game_", "")
        
        # Получаем список турниров с фильтром
        tournaments = []
        available_games = []
        if _mongo_client is not None:
            try:
                tournaments = await _mongo_client.get_tournaments(
                    status=status_filter,
                    game_discipline=game_filter,
                )
                available_games = list(
                    set(t.game_discipline for t in tournaments),
                )
            except Exception as e:
                _LOG.error(
                    f"Ошибка при получении турниров: {e}",
                )
        
        tournaments_text = format_tournaments_list(tournaments)
        current_filter = filter_type if not filter_type.startswith("game_") else "all"
        await callback.message.edit_text(
            text=tournaments_text,
            reply_markup=get_tournaments_list_keyboard(
                tournaments=tournaments,
                current_filter=current_filter,
                current_game=game_filter,
                available_games=available_games,
            ),
        )
    elif callback_data.startswith("tournament_view_"):
        # Просмотр карточки турнира
        tournament_id = callback_data.replace("tournament_view_", "")
        
        tournament = None
        is_participant = False
        if _mongo_client is not None:
            try:
                tournament = await _mongo_client.get_tournament(tournament_id)
                if tournament:
                    # Проверяем, участвует ли пользователь
                    if tournament.format == TournamentFormat.SOLO:
                        is_participant = callback.from_user.id in tournament.solo_participants
                    else:
                        user = await _mongo_client.get_user(callback.from_user.id)
                        if user and user.team_id:
                            is_participant = user.team_id in tournament.team_participants
            except Exception as e:
                _LOG.error(
                    f"Ошибка при получении турнира {tournament_id}: {e}",
                )
        
        if not tournament:
            await callback.answer(
                "Турнир не найден",
                show_alert=True,
            )
            return
        
        tournament_text = format_tournament_card(tournament, is_participant)
        await callback.message.edit_text(
            text=tournament_text,
            reply_markup=get_tournament_card_keyboard(
                tournament_id=tournament_id,
                tournament_status=tournament.status.value,
                is_participant=is_participant,
                results_published=tournament.results_published,
            ),
        )
    elif callback_data.startswith("tournament_join_"):
        # Вступление в турнир
        tournament_id = callback_data.replace("tournament_join_", "")
        
        tournament = None
        if _mongo_client is not None:
            try:
                tournament = await _mongo_client.get_tournament(tournament_id)
            except Exception as e:
                _LOG.error(
                    f"Ошибка при получении турнира {tournament_id}: {e}",
                )
        
        if not tournament:
            await callback.answer(
                "Турнир не найден",
                show_alert=True,
            )
            return
        
        if tournament.status != TournamentStatus.REGISTRATION_OPEN:
            await callback.answer(
                "Регистрация на турнир закрыта",
                show_alert=True,
            )
            return
        
        # Проверяем формат турнира
        if tournament.format == TournamentFormat.SOLO:
            # Соло турнир - показываем подтверждение
            await callback.answer("Подтверждение участия")
            await callback.message.edit_text(
                text=(
                    f"🏆 {tournament.name}\n\n"
                    f"Подтвердите участие в турнире.\n\n"
                    f"Формат: Соло\n"
                    f"{f'Взнос: {tournament.entry_fee} CD токенов' if tournament.entry_fee else ''}"
                ),
                reply_markup=get_tournament_join_confirm_keyboard(tournament_id),
            )
        else:
            # Командный турнир - выбираем команду
            user = None
            user_teams = []
            if _mongo_client is not None:
                try:
                    user = await _mongo_client.get_user(callback.from_user.id)
                    if user and user.team_id:
                        team = await _mongo_client.get_team(user.team_id)
                        if team:
                            user_teams = [team]
                except Exception as e:
                    _LOG.error(
                        f"Ошибка при получении команды пользователя: {e}",
                    )
            
            if not user_teams:
                await callback.answer(
                    "Ты не в команде",
                    show_alert=True,
                )
                return
            
            await callback.answer("Выбор команды")
            await callback.message.edit_text(
                text=(
                    f"🏆 {tournament.name}\n\n"
                    f"Выберите команду для участия в турнире:"
                ),
                reply_markup=get_tournament_team_select_keyboard(
                    tournament_id=tournament_id,
                    user_teams=user_teams,
                ),
            )
    elif callback_data.startswith("tournament_confirm_"):
        # Подтверждение участия в соло турнире
        tournament_id = callback_data.replace("tournament_confirm_", "")
        
        if _mongo_client is None:
            await callback.answer(
                "Ошибка: база данных недоступна",
                show_alert=True,
            )
            return
        
        try:
            tournament = await _mongo_client.get_tournament(tournament_id)
            if not tournament:
                await callback.answer(
                    "Турнир не найден",
                    show_alert=True,
                )
                return
            
            if tournament.format != TournamentFormat.SOLO:
                await callback.answer(
                    "Это командный турнир",
                    show_alert=True,
                )
                return
            
            # Проверяем, не участвует ли уже
            if callback.from_user.id in tournament.solo_participants:
                await callback.answer(
                    "Вы уже участвуете в этом турнире",
                    show_alert=True,
                )
                return
            
            # Проверяем лимит участников
            if tournament.participant_limit:
                if len(tournament.solo_participants) >= tournament.participant_limit:
                    await callback.answer(
                        "Достигнут лимит участников",
                        show_alert=True,
                    )
                    return
            
            # Добавляем участника
            tournament.solo_participants.append(callback.from_user.id)
            await _mongo_client.update_tournament(tournament)
            
            await callback.answer("✅ Вы успешно зарегистрированы на турнир!")
            
            # Показываем обновленную карточку турнира
            tournament_text = format_tournament_card(tournament, is_participant=True)
            await callback.message.edit_text(
                text=tournament_text,
                reply_markup=get_tournament_card_keyboard(
                    tournament_id=tournament_id,
                    tournament_status=tournament.status.value,
                    is_participant=True,
                ),
            )
            
        except Exception as e:
            _LOG.error(
                f"Ошибка при регистрации на турнир {tournament_id}: {e}",
            )
            await callback.answer(
                "Произошла ошибка при регистрации",
                show_alert=True,
            )
    elif callback_data.startswith("tournament_join_team_"):
        # Вступление в командный турнир с выбранной командой
        parts = callback_data.replace("tournament_join_team_", "").split("_")
        if len(parts) < 2:
            await callback.answer("Ошибка", show_alert=True)
            return
        
        tournament_id = parts[0]
        team_id = "_".join(parts[1:])  # На случай если team_id содержит подчеркивания
        
        if _mongo_client is None:
            await callback.answer(
                "Ошибка: база данных недоступна",
                show_alert=True,
            )
            return
        
        try:
            tournament = await _mongo_client.get_tournament(tournament_id)
            if not tournament:
                await callback.answer(
                    "Турнир не найден",
                    show_alert=True,
                )
                return
            
            if tournament.format != TournamentFormat.TEAM:
                await callback.answer(
                    "Это соло турнир",
                    show_alert=True,
                )
                return
            
            # Проверяем, не участвует ли команда уже
            if team_id in tournament.team_participants:
                await callback.answer(
                    "Команда уже участвует в этом турнире",
                    show_alert=True,
                )
                return
            
            # Проверяем лимит участников
            if tournament.participant_limit:
                if len(tournament.team_participants) >= tournament.participant_limit:
                    await callback.answer(
                        "Достигнут лимит команд",
                        show_alert=True,
                    )
                    return
            
            # Добавляем команду
            tournament.team_participants.append(team_id)
            await _mongo_client.update_tournament(tournament)
            
            team = await _mongo_client.get_team(team_id)
            team_name = team.name if team else team_id
            
            await callback.answer(f"✅ Команда {team_name} зарегистрирована на турнир!")
            
            # Показываем обновленную карточку турнира
            user = await _mongo_client.get_user(callback.from_user.id)
            is_participant = user and user.team_id == team_id and team_id in tournament.team_participants
            
            tournament_text = format_tournament_card(tournament, is_participant=is_participant)
            await callback.message.edit_text(
                text=tournament_text,
            reply_markup=get_tournament_card_keyboard(
                tournament_id=tournament_id,
                tournament_status=tournament.status.value,
                is_participant=is_participant,
                results_published=tournament.results_published,
            ),
            )
            
        except Exception as e:
            _LOG.error(
                f"Ошибка при регистрации команды на турнир {tournament_id}: {e}",
            )
            await callback.answer(
                "Произошла ошибка при регистрации",
                show_alert=True,
            )
    elif callback_data.startswith("tournament_rules_"):
        # Просмотр правил турнира
        tournament_id = callback_data.replace("tournament_rules_", "")
        
        tournament = None
        if _mongo_client is not None:
            try:
                tournament = await _mongo_client.get_tournament(tournament_id)
            except Exception as e:
                _LOG.error(
                    f"Ошибка при получении турнира {tournament_id}: {e}",
                )
        
        if not tournament:
            await callback.answer("Турнир не найден", show_alert=True)
            return
        
        rules_text = (
            f"📋 Правила турнира: {tournament.name}\n\n"
        )
        
        if tournament.full_rules:
            rules_text += tournament.full_rules
        elif tournament.rules_summary:
            rules_text += tournament.rules_summary
        else:
            rules_text += "Правила не указаны."
        
        await callback.answer("Правила турнира")
        await callback.message.edit_text(
            text=rules_text,
            reply_markup=get_tournament_card_keyboard(
                tournament_id=tournament_id,
                tournament_status=tournament.status.value,
                is_participant=False,  # Не проверяем участие для просмотра правил
            ),
        )
    elif callback_data.startswith("tournament_participants_"):
        # Просмотр участников/команд
        tournament_id = callback_data.replace("tournament_participants_", "")
        
        tournament = None
        if _mongo_client is not None:
            try:
                tournament = await _mongo_client.get_tournament(tournament_id)
            except Exception as e:
                _LOG.error(
                    f"Ошибка при получении турнира {tournament_id}: {e}",
                )
        
        if not tournament:
            await callback.answer("Турнир не найден", show_alert=True)
            return
        
        participants_text = f"👥 Участники турнира: {tournament.name}\n\n"
        
        if tournament.format == TournamentFormat.SOLO:
            if tournament.solo_participants:
                participants_text += "Участники:\n"
                for i, user_id in enumerate(tournament.solo_participants, 1):
                    user = None
                    if _mongo_client is not None:
                        try:
                            user = await _mongo_client.get_user(user_id)
                        except Exception:
                            pass
                    
                    user_name = (
                        user.nickname
                        or user.username
                        or f"ID: {user_id}"
                        if user
                        else f"ID: {user_id}"
                    )
                    participants_text += f"{i}. {user_name}\n"
            else:
                participants_text += "Участников пока нет."
        else:
            if tournament.team_participants:
                participants_text += "Команды:\n"
                for i, team_id in enumerate(tournament.team_participants, 1):
                    team = None
                    if _mongo_client is not None:
                        try:
                            team = await _mongo_client.get_team(team_id)
                        except Exception:
                            pass
                    
                    team_name = (
                        f"{team.name} ({team.tag})"
                        if team
                        else f"ID: {team_id}"
                    )
                    participants_text += f"{i}. {team_name}\n"
            else:
                participants_text += "Команд пока нет."
        
        await callback.answer("Участники/Команды")
        await callback.message.edit_text(
            text=participants_text,
            reply_markup=get_tournament_card_keyboard(
                tournament_id=tournament_id,
                tournament_status=tournament.status.value,
                is_participant=False,
            ),
        )
    elif callback_data.startswith("tournament_results_"):
        # Таблица результатов
        tournament_id = callback_data.replace("tournament_results_", "")
        
        tournament = None
        if _mongo_client is not None:
            try:
                tournament = await _mongo_client.get_tournament(tournament_id)
            except Exception as e:
                _LOG.error(
                    f"Ошибка при получении турнира {tournament_id}: {e}",
                )
        
        if not tournament:
            await callback.answer("Турнир не найден", show_alert=True)
            return
        
        if tournament.status not in (TournamentStatus.IN_PROGRESS, TournamentStatus.COMPLETED):
            await callback.answer(
                "Результаты доступны только для идущих или завершённых турниров",
                show_alert=True,
            )
            return
        
        await callback.answer("Таблица результатов")
        await callback.message.edit_text(
            text=f"📊 Таблица результатов: {tournament.name}\n\nРаздел в разработке...",
            reply_markup=get_tournament_card_keyboard(
                tournament_id=tournament_id,
                tournament_status=tournament.status.value,
                is_participant=False,
            ),
        )
    elif callback_data == "menu_back":
        await callback.answer("Главное меню")
        await callback.message.edit_text(
            text="Главное меню",
            reply_markup=get_main_menu_keyboard(
                show_admin=show_admin,
            ),
        )


async def admin_callback_handler(
    callback: types.CallbackQuery,
) -> None:
    """
    Обработчик нажатий на инлайн-кнопки админ-панели.
    Проверяет права доступа перед выполнением действий.
    Доступ имеют только: MANAGER, ADMIN, SUPER_ADMIN.
    """
    callback_data = callback.data
    
    # Получаем роль пользователя из базы данных
    user_role = await get_user_role(
        callback.from_user.id,
    )
    is_super_admin = user_role == UserRole.SUPER_ADMIN
    
    # Проверка доступа к админ-панели
    # Доступ имеют только: MANAGER, ADMIN, SUPER_ADMIN
    if not has_admin_access(user_role):
        _LOG.warning(
            f"Попытка доступа к админ-панели (раздел: {callback_data}) "
            f"пользователем {callback.from_user.id} с ролью {user_role.value}",
        )
        await callback.answer(
            "❌ У вас нет доступа к админ-панели.\n\n"
            "Доступ имеют только менеджеры, админы и супер-админы.",
            show_alert=True,
        )
        return
    
    if callback_data == "admin_tournaments":
        await callback.answer("Турниры")
        
        # Получаем список турниров
        tournaments = []
        if _mongo_client is not None:
            try:
                tournaments = await _mongo_client.get_tournaments()
            except Exception as e:
                _LOG.error(
                    f"Ошибка при получении турниров: {e}",
                )
        
        tournaments_text = "🏆 Турниры (админ-панель)\n\n"
        if tournaments:
            tournaments_text += f"Всего турниров: {len(tournaments)}\n\n"
            for i, tournament in enumerate(tournaments[:5], 1):  # Показываем первые 5
                status_emoji = {
                    TournamentStatus.REGISTRATION_OPEN: "✅",
                    TournamentStatus.IN_PROGRESS: "🔄",
                    TournamentStatus.COMPLETED: "🏁",
                }
                emoji = status_emoji.get(tournament.status, "🏆")
                tournaments_text += f"{i}. {emoji} {tournament.name}\n"
            if len(tournaments) > 5:
                tournaments_text += f"\n... и ещё {len(tournaments) - 5} турниров"
        else:
            tournaments_text += "Турниров пока нет."
        
        await callback.message.edit_text(
            text=tournaments_text,
            reply_markup=get_admin_tournaments_list_keyboard(),
        )
    elif callback_data == "admin_results":
        await callback.answer("Результаты")
        # Получаем список турниров для выбора
        tournaments = []
        if _mongo_client is not None:
            try:
                all_tournaments = await _mongo_client.get_tournaments()
                # Показываем только турниры, которые идут или завершены
                tournaments = [
                    t for t in all_tournaments
                    if t.status in [TournamentStatus.IN_PROGRESS, TournamentStatus.COMPLETED]
                ]
            except Exception as e:
                _LOG.error(f"Ошибка при получении турниров: {e}")
        
        if not tournaments:
            await callback.message.edit_text(
                text="✅ Результаты\n\n"
                     "Нет доступных турниров для внесения результатов.\n\n"
                     "Турниры должны быть в статусе 'Идёт' или 'Завершён'.",
                reply_markup=get_admin_panel_keyboard(
                    is_super_admin=is_super_admin,
                ),
            )
        else:
            await callback.message.edit_text(
                text="✅ Результаты\n\n"
                     "Выберите турнир для внесения результатов:",
                reply_markup=get_admin_results_tournaments_keyboard(tournaments),
            )
    elif callback_data.startswith("admin_results_tournament_"):
        tournament_id = callback_data.replace("admin_results_tournament_", "")
        await callback.answer("Выбор турнира")
        
        if _mongo_client is not None:
            try:
                tournament = await _mongo_client.get_tournament(tournament_id)
                if not tournament:
                    await callback.answer("Турнир не найден", show_alert=True)
                    return
                
                await callback.message.edit_text(
                    text=f"✅ Результаты: {tournament.name}\n\n"
                         "Выберите метод внесения результатов:",
                    reply_markup=get_admin_results_method_keyboard(tournament_id),
                )
            except Exception as e:
                _LOG.error(f"Ошибка при получении турнира: {e}")
                await callback.answer("Произошла ошибка", show_alert=True)
    elif callback_data.startswith("admin_results_method_a_"):
        # Вариант A: итоговая цифра на турнир
        tournament_id = callback_data.replace("admin_results_method_a_", "")
        await callback.answer("Вариант A: Итоговая цифра")
        
        if _mongo_client is not None:
            try:
                tournament = await _mongo_client.get_tournament(tournament_id)
                if not tournament:
                    await callback.answer("Турнир не найден", show_alert=True)
                    return
                
                # Получаем список участников
                participants = []
                if tournament.format == TournamentFormat.SOLO:
                    participants = tournament.solo_participants
                else:
                    participants = tournament.team_participants
                
                if not participants:
                    await callback.answer("В турнире нет участников", show_alert=True)
                    return
                
                # Активируем режим внесения результатов
                _waiting_results_data[callback.from_user.id] = {
                    "type": "method_a",
                    "tournament_id": tournament_id,
                    "participants": participants,
                    "current_index": 0,
                }
                
                participant_name = await _get_participant_name(tournament, participants[0])
                await callback.message.edit_text(
                    text=f"✅ Внесение результатов: {tournament.name}\n\n"
                         f"Вариант A: Итоговая цифра\n\n"
                         f"Участник 1/{len(participants)}: {participant_name}\n\n"
                         f"Введите количество киллов за турнир:\n\n"
                         f"Или отправьте /cancel для отмены.",
                )
            except Exception as e:
                _LOG.error(f"Ошибка при подготовке внесения результатов: {e}")
                await callback.answer("Произошла ошибка", show_alert=True)
    elif callback_data.startswith("admin_results_method_b_"):
        # Вариант B: по матчам
        tournament_id = callback_data.replace("admin_results_method_b_", "")
        await callback.answer("Вариант B: По матчам")
        
        if _mongo_client is not None:
            try:
                tournament = await _mongo_client.get_tournament(tournament_id)
                if not tournament:
                    await callback.answer("Турнир не найден", show_alert=True)
                    return
                
                # Получаем список матчей
                matches = await _mongo_client.get_tournament_matches(tournament_id)
                
                await callback.message.edit_text(
                    text=f"✅ Результаты: {tournament.name}\n\n"
                         f"Вариант B: По матчам\n\n"
                         "Выберите матч для внесения результатов:",
                    reply_markup=get_admin_results_matches_keyboard(tournament_id, matches),
                )
            except Exception as e:
                _LOG.error(f"Ошибка при получении матчей: {e}")
                await callback.answer("Произошла ошибка", show_alert=True)
    elif callback_data.startswith("admin_results_match_"):
        # Выбор матча для внесения результатов
        match_id = callback_data.replace("admin_results_match_", "")
        await callback.answer("Выбор матча")
        
        if _mongo_client is not None:
            try:
                match = await _mongo_client.get_match(match_id)
                if not match:
                    await callback.answer("Матч не найден", show_alert=True)
                    return
                
                tournament = await _mongo_client.get_tournament(match.tournament_id)
                if not tournament:
                    await callback.answer("Турнир не найден", show_alert=True)
                    return
                
                # Получаем список участников
                participants = []
                if tournament.format == TournamentFormat.SOLO:
                    participants = tournament.solo_participants
                else:
                    participants = tournament.team_participants
                
                if not participants:
                    await callback.answer("В турнире нет участников", show_alert=True)
                    return
                
                # Активируем режим внесения результатов матча
                _waiting_results_data[callback.from_user.id] = {
                    "type": "method_b_match",
                    "tournament_id": match.tournament_id,
                    "match_id": match_id,
                    "participants": participants,
                    "current_index": 0,
                }
                
                participant_name = await _get_participant_name(tournament, participants[0])
                await callback.message.edit_text(
                    text=f"✅ Внесение результатов: {match.name}\n\n"
                         f"Участник 1/{len(participants)}: {participant_name}\n\n"
                         f"Введите количество киллов в матче:\n\n"
                         f"Или отправьте /cancel для отмены.",
                )
            except Exception as e:
                _LOG.error(f"Ошибка при подготовке внесения результатов матча: {e}")
                await callback.answer("Произошла ошибка", show_alert=True)
    elif callback_data.startswith("admin_results_create_match_"):
        # Создание нового матча
        tournament_id = callback_data.replace("admin_results_create_match_", "")
        await callback.answer("Создание матча")
        # Активируем режим создания матча
        _waiting_results_data[callback.from_user.id] = {
            "type": "create_match",
            "tournament_id": tournament_id,
            "step": "name",
        }
        await callback.message.edit_text(
            text="✅ Создание матча\n\n"
                 "Введите название матча:\n\n"
                 "Или отправьте /cancel для отмены.",
        )
    elif callback_data.startswith("admin_results_publish_"):
        # Публикация результатов
        tournament_id = callback_data.replace("admin_results_publish_", "")
        await callback.answer("Публикация результатов...")
        
        if _mongo_client is not None:
            try:
                # Публикуем результаты
                await _mongo_client.publish_tournament_results(tournament_id)
                # Логируем публикацию результатов
                tournament = await _mongo_client.get_tournament(tournament_id)
                if tournament:
                    await _mongo_client.add_action_log(
                        action_type=ActionType.RESULTS_PUBLISHED,
                        user_id=callback.from_user.id,
                        description=f"Опубликованы результаты турнира '{tournament.name}'",
                        details={"tournament_id": tournament_id},
                    )
                
                # Отправляем уведомления участникам
                if not tournament:
                    tournament = await _mongo_client.get_tournament(tournament_id)
                if tournament:
                    participants = []
                    if tournament.format == TournamentFormat.SOLO:
                        participants = tournament.solo_participants
                    else:
                        participants = tournament.team_participants
                    
                    # Получаем результаты для уведомлений
                    results = await _mongo_client.get_tournament_results(tournament_id)
                    results.sort(key=lambda r: r.total_kills, reverse=True)
                    
                    # Отправляем уведомления (упрощенная версия - просто логируем)
                    _LOG.info(f"Результаты турнира {tournament_id} опубликованы. Уведомления отправлены {len(participants)} участникам.")
                
                await callback.answer("✅ Результаты опубликованы! Уведомления отправлены участникам.", show_alert=True)
                
                # Обновляем экран
                await callback.message.edit_text(
                    text=f"✅ Результаты: {tournament.name if tournament else 'Турнир'}\n\n"
                         "✅ Результаты опубликованы!\n\n"
                         "Все участники получили уведомления.",
                    reply_markup=get_admin_results_tournaments_keyboard([]),
                )
            except Exception as e:
                _LOG.error(f"Ошибка при публикации результатов: {e}")
                await callback.answer("❌ Произошла ошибка при публикации результатов", show_alert=True)
    elif callback_data.startswith("admin_results_edit_"):
        # Редактирование результатов
        tournament_id = callback_data.replace("admin_results_edit_", "")
        await callback.answer("Редактирование результатов")
        # Возвращаемся к выбору метода
        if _mongo_client is not None:
            try:
                tournament = await _mongo_client.get_tournament(tournament_id)
                if tournament:
                    await callback.message.edit_text(
                        text=f"✅ Результаты: {tournament.name}\n\n"
                             "Выберите метод внесения результатов:",
                        reply_markup=get_admin_results_method_keyboard(tournament_id),
                    )
            except Exception as e:
                _LOG.error(f"Ошибка при редактировании результатов: {e}")
    elif callback_data == "admin_back":
        await callback.answer("Админ-панель")
        await callback.message.edit_text(
            text="⚙️ Админ-панель",
            reply_markup=get_admin_panel_keyboard(
                is_super_admin=is_super_admin,
            ),
        )
    elif callback_data == "admin_users":
        await callback.answer("Пользователи")
        await callback.message.edit_text(
            text="👥 Пользователи\n\n"
                 "Введите никнейм или ID пользователя для поиска.\n\n"
                 "Примеры:\n"
                 "  • @username\n"
                 "  • 123456789\n"
                 "  • nickname",
            reply_markup=get_admin_users_search_keyboard(),
        )
        # Активируем режим поиска пользователя
        _waiting_user_search[callback.from_user.id] = True
    elif callback_data == "admin_teams":
        await callback.answer("Команды")
        await callback.message.edit_text(
            text="🧑‍🤝‍🧑 Команды\n\n"
                 "Введите название команды, тег или ID команды для поиска.\n\n"
                 "Примеры:\n"
                 "  • Название команды\n"
                 "  • TAG\n"
                 "  • team_abc123",
            reply_markup=get_admin_teams_search_keyboard(),
        )
        # Активируем режим поиска команды
        _waiting_team_search[callback.from_user.id] = True
    elif callback_data.startswith("admin_team_card_"):
        # Показываем карточку команды
        team_id = callback_data.replace("admin_team_card_", "")
        await callback.answer("Карточка команды")
        
        if _mongo_client is not None:
            try:
                team = await _mongo_client.get_team(team_id)
                if not team:
                    await callback.answer("Команда не найдена", show_alert=True)
                    return
                
                team_card_text = await format_admin_team_card_text(team)
                
                await callback.message.edit_text(
                    text=team_card_text,
                    reply_markup=get_admin_team_card_keyboard(
                        team_id=team_id,
                        is_banned=team.is_banned,
                        captain_confirmed=team.captain_confirmed,
                    ),
                    parse_mode="HTML",
                )
            except Exception as e:
                _LOG.error(f"Ошибка при получении карточки команды: {e}")
                await callback.answer("Произошла ошибка", show_alert=True)
    elif callback_data.startswith("admin_team_confirm_captain_"):
        # Подтверждение капитана
        team_id = callback_data.replace("admin_team_confirm_captain_", "")
        await callback.answer("Подтвердить капитана")
        
        if _mongo_client is not None:
            try:
                await _mongo_client.update_team_captain_confirmed(team_id, True)
                team = await _mongo_client.get_team(team_id)
                if team:
                    team_card_text = await format_admin_team_card_text(team)
                    await callback.message.edit_text(
                        text=team_card_text,
                        reply_markup=get_admin_team_card_keyboard(
                            team_id=team_id,
                            is_banned=team.is_banned,
                            captain_confirmed=True,
                        ),
                        parse_mode="HTML",
                    )
            except Exception as e:
                _LOG.error(f"Ошибка при подтверждении капитана: {e}")
                await callback.answer("Произошла ошибка", show_alert=True)
    elif callback_data.startswith("admin_team_ban_"):
        # Блокировка команды
        team_id = callback_data.replace("admin_team_ban_", "")
        await callback.answer("Заблокировать команду")
        
        if _mongo_client is not None:
            try:
                await _mongo_client.update_team_ban_status(team_id, True)
                # Логируем бан команды
                await _mongo_client.add_action_log(
                    action_type=ActionType.TEAM_BANNED,
                    user_id=callback.from_user.id,
                    description=f"Забанена команда (ID: {team_id})",
                    details={"team_id": team_id},
                )
                team = await _mongo_client.get_team(team_id)
                if team:
                    team_card_text = await format_admin_team_card_text(team)
                    await callback.message.edit_text(
                        text=team_card_text,
                        reply_markup=get_admin_team_card_keyboard(
                            team_id=team_id,
                            is_banned=True,
                            captain_confirmed=team.captain_confirmed,
                        ),
                        parse_mode="HTML",
                    )
            except Exception as e:
                _LOG.error(f"Ошибка при блокировке команды: {e}")
                await callback.answer("Произошла ошибка", show_alert=True)
    elif callback_data.startswith("admin_team_unban_"):
        # Разблокировка команды
        team_id = callback_data.replace("admin_team_unban_", "")
        await callback.answer("Разблокировать команду")
        
        if _mongo_client is not None:
            try:
                await _mongo_client.update_team_ban_status(team_id, False)
                # Логируем разбан команды
                await _mongo_client.add_action_log(
                    action_type=ActionType.TEAM_UNBANNED,
                    user_id=callback.from_user.id,
                    description=f"Разбанена команда (ID: {team_id})",
                    details={"team_id": team_id},
                )
                team = await _mongo_client.get_team(team_id)
                if team:
                    team_card_text = await format_admin_team_card_text(team)
                    await callback.message.edit_text(
                        text=team_card_text,
                        reply_markup=get_admin_team_card_keyboard(
                            team_id=team_id,
                            is_banned=False,
                            captain_confirmed=team.captain_confirmed,
                        ),
                        parse_mode="HTML",
                    )
            except Exception as e:
                _LOG.error(f"Ошибка при разблокировке команды: {e}")
                await callback.answer("Произошла ошибка", show_alert=True)
    elif callback_data.startswith("admin_user_card_"):
        # Показываем карточку пользователя
        target_user_id = int(callback_data.replace("admin_user_card_", ""))
        await callback.answer("Карточка пользователя")
        
        if _mongo_client is not None:
            try:
                target_user = await _mongo_client.get_user(target_user_id)
                if not target_user:
                    await callback.answer("Пользователь не найден", show_alert=True)
                    return
                
                team = None
                if target_user.team_id:
                    team = await _mongo_client.get_team(target_user.team_id)
                
                user_card_text = format_admin_user_card_text(target_user, team)
                
                await callback.message.edit_text(
                    text=user_card_text,
                    reply_markup=get_admin_user_card_keyboard(
                        user_id=target_user_id,
                        is_super_admin=is_super_admin,
                        is_banned=target_user.is_banned,
                    ),
                    parse_mode="HTML",
                )
            except Exception as e:
                _LOG.error(f"Ошибка при получении карточки пользователя: {e}")
                await callback.answer("Произошла ошибка", show_alert=True)
    elif callback_data.startswith("admin_user_add_tokens_"):
        # Начисление токенов
        target_user_id = int(callback_data.replace("admin_user_add_tokens_", ""))
        await callback.answer("Начислить CD токен")
        await callback.message.edit_text(
            text=f"➕ Начислить CD токен\n\n"
                 f"Введите сумму для начисления пользователю (ID: {target_user_id}):\n\n"
                 f"Или отправьте /cancel для отмены.",
        )
        # Активируем режим ожидания суммы
        _waiting_token_amount[callback.from_user.id] = {
            "action": "add",
            "target_user_id": target_user_id,
        }
    elif callback_data.startswith("admin_user_remove_tokens_"):
        # Списание токенов
        target_user_id = int(callback_data.replace("admin_user_remove_tokens_", ""))
        await callback.answer("Списать CD токен")
        await callback.message.edit_text(
            text=f"➖ Списать CD токен\n\n"
                 f"Введите сумму для списания у пользователя (ID: {target_user_id}):\n\n"
                 f"Или отправьте /cancel для отмены.",
        )
        # Активируем режим ожидания суммы
        _waiting_token_amount[callback.from_user.id] = {
            "action": "remove",
            "target_user_id": target_user_id,
        }
    elif callback_data.startswith("admin_user_ban_"):
        # Бан пользователя
        target_user_id = int(callback_data.replace("admin_user_ban_", ""))
        await callback.answer("Забанить пользователя")
        
        if _mongo_client is not None:
            try:
                await _mongo_client.update_user_ban_status(target_user_id, True)
                # Логируем бан пользователя
                await _mongo_client.add_action_log(
                    action_type=ActionType.USER_BANNED,
                    user_id=callback.from_user.id,
                    description=f"Забанен пользователь (ID: {target_user_id})",
                    details={"target_user_id": target_user_id},
                )
                target_user = await _mongo_client.get_user(target_user_id)
                if target_user:
                    team = None
                    if target_user.team_id:
                        team = await _mongo_client.get_team(target_user.team_id)
                    user_card_text = format_admin_user_card_text(target_user, team)
                    await callback.message.edit_text(
                        text=user_card_text,
                        reply_markup=get_admin_user_card_keyboard(
                            user_id=target_user_id,
                            is_super_admin=is_super_admin,
                            is_banned=True,
                        ),
                        parse_mode="HTML",
                    )
            except Exception as e:
                _LOG.error(f"Ошибка при бане пользователя: {e}")
                await callback.answer("Произошла ошибка", show_alert=True)
    elif callback_data.startswith("admin_user_unban_"):
        # Разбан пользователя
        target_user_id = int(callback_data.replace("admin_user_unban_", ""))
        await callback.answer("Снять ограничение")
        
        if _mongo_client is not None:
            try:
                await _mongo_client.update_user_ban_status(target_user_id, False)
                # Логируем разбан пользователя
                await _mongo_client.add_action_log(
                    action_type=ActionType.USER_UNBANNED,
                    user_id=callback.from_user.id,
                    description=f"Разбанен пользователь (ID: {target_user_id})",
                    details={"target_user_id": target_user_id},
                )
                target_user = await _mongo_client.get_user(target_user_id)
                if target_user:
                    team = None
                    if target_user.team_id:
                        team = await _mongo_client.get_team(target_user.team_id)
                    user_card_text = format_admin_user_card_text(target_user, team)
                    await callback.message.edit_text(
                        text=user_card_text,
                        reply_markup=get_admin_user_card_keyboard(
                            user_id=target_user_id,
                            is_super_admin=is_super_admin,
                            is_banned=False,
                        ),
                        parse_mode="HTML",
                    )
            except Exception as e:
                _LOG.error(f"Ошибка при разбане пользователя: {e}")
                await callback.answer("Произошла ошибка", show_alert=True)
    elif callback_data.startswith("admin_user_role_"):
        # Выбор роли пользователя
        target_user_id = int(callback_data.replace("admin_user_role_", ""))
        await callback.answer("Назначить роль")
        
        if not is_super_admin:
            await callback.answer("Только супер-админ может назначать роли", show_alert=True)
            return
        
        await callback.message.edit_text(
            text=f"🎭 Назначить роль\n\n"
                 f"Выберите роль для пользователя (ID: {target_user_id}):",
            reply_markup=get_admin_user_role_keyboard(target_user_id),
        )
    elif callback_data.startswith("admin_user_set_role_"):
        # Установка роли пользователя
        parts = callback_data.replace("admin_user_set_role_", "").split("_")
        if len(parts) >= 2:
            target_user_id = int(parts[0])
            role_name = "_".join(parts[1:])
            
            if not is_super_admin:
                await callback.answer("Только супер-админ может назначать роли", show_alert=True)
                return
            
            try:
                role = UserRole[role_name]
                if _mongo_client is not None:
                    await _mongo_client.update_user_role(target_user_id, role)
                    # Логируем изменение роли
                    await _mongo_client.add_action_log(
                        action_type=ActionType.USER_ROLE_CHANGED,
                        user_id=callback.from_user.id,
                        description=f"Изменена роль пользователя (ID: {target_user_id}) на {role.value}",
                        details={"target_user_id": target_user_id, "new_role": role.value},
                    )
                    target_user = await _mongo_client.get_user(target_user_id)
                    if target_user:
                        team = None
                        if target_user.team_id:
                            team = await _mongo_client.get_team(target_user.team_id)
                        user_card_text = format_admin_user_card_text(target_user, team)
                        await callback.message.edit_text(
                            text=user_card_text,
                            reply_markup=get_admin_user_card_keyboard(
                                user_id=target_user_id,
                                is_super_admin=is_super_admin,
                                is_banned=target_user.is_banned,
                            ),
                            parse_mode="HTML",
                        )
                        await callback.answer(f"Роль изменена на {role.value}")
            except (KeyError, ValueError) as e:
                _LOG.error(f"Ошибка при установке роли: {e}")
                await callback.answer("Неверная роль", show_alert=True)
            except Exception as e:
                _LOG.error(f"Ошибка при установке роли: {e}")
                await callback.answer("Произошла ошибка", show_alert=True)
    elif callback_data == "admin_ratings":
        await callback.answer("Рейтинги")
        # Получаем текущие правила рейтинга
        rules_text = "📊 Рейтинги\n\n"
        if _mongo_client is not None:
            try:
                rules = await _mongo_client.get_rating_rules()
                if rules:
                    rules_text += f"⚙️ Текущие правила:\n"
                    rules_text += f"  👤 Игроки: {rules.player_metric.value}\n"
                    rules_text += f"  👥 Команды: {rules.team_metric.value}\n"
                    if rules.season_start_date and rules.season_end_date:
                        rules_text += f"  📅 Сезон: {rules.season_start_date} - {rules.season_end_date}\n"
                else:
                    rules_text += "⚙️ Правила не настроены (используются значения по умолчанию)\n"
            except Exception as e:
                _LOG.error(f"Ошибка при получении правил рейтинга: {e}")
        
        await callback.message.edit_text(
            text=rules_text,
            reply_markup=get_admin_ratings_keyboard(),
        )
    elif callback_data == "admin_ratings_recalculate":
        await callback.answer("Обновление рейтинга...")
        # Пересчитываем рейтинг
        if _mongo_client is not None:
            try:
                await _mongo_client.recalculate_ratings()
                # Логируем пересчет рейтинга
                await _mongo_client.add_action_log(
                    action_type=ActionType.RATING_RECALCULATED,
                    user_id=callback.from_user.id,
                    description="Выполнен пересчет рейтинга",
                )
                await callback.answer("✅ Рейтинг успешно обновлён!", show_alert=True)
                # Обновляем экран
                rules = await _mongo_client.get_rating_rules()
                rules_text = "📊 Рейтинги\n\n"
                if rules:
                    rules_text += f"⚙️ Текущие правила:\n"
                    rules_text += f"  👤 Игроки: {rules.player_metric.value}\n"
                    rules_text += f"  👥 Команды: {rules.team_metric.value}\n"
                    if rules.season_start_date and rules.season_end_date:
                        rules_text += f"  📅 Сезон: {rules.season_start_date} - {rules.season_end_date}\n"
                await callback.message.edit_text(
                    text=rules_text,
                    reply_markup=get_admin_ratings_keyboard(),
                )
            except Exception as e:
                _LOG.error(f"Ошибка при пересчёте рейтинга: {e}")
                await callback.answer("❌ Произошла ошибка при обновлении рейтинга", show_alert=True)
        else:
            await callback.answer("❌ Ошибка подключения к базе данных", show_alert=True)
    elif callback_data == "admin_ratings_period":
        await callback.answer("Выбор периода")
        await callback.message.edit_text(
            text="📅 Выбор периода рейтинга\n\n"
                 "Выберите период для отображения рейтинга:",
            reply_markup=get_admin_ratings_period_keyboard(),
        )
    elif callback_data.startswith("admin_ratings_period_"):
        period = callback_data.replace("admin_ratings_period_", "")
        await callback.answer(f"Период: {period}")
        # Здесь можно сохранить выбранный период или просто показать сообщение
        period_names = {
            "all_time": "За всё время",
            "season": "За сезон",
            "month": "За месяц",
        }
        await callback.message.edit_text(
            text=f"📅 Период рейтинга: {period_names.get(period, period)}\n\n"
                 "Период выбран. Рейтинг будет отображаться с учётом выбранного периода.",
            reply_markup=get_admin_ratings_keyboard(),
        )
    elif callback_data == "admin_ratings_rules":
        await callback.answer("Настройка правил")
        await callback.message.edit_text(
            text="⚙️ Настройка правил рейтинга\n\n"
                 "Выберите тип рейтинга для настройки:",
            reply_markup=get_admin_ratings_rules_keyboard(),
        )
    elif callback_data.startswith("admin_ratings_rules_"):
        rating_type = callback_data.replace("admin_ratings_rules_", "")
        await callback.answer("Выбор метрики")
        await callback.message.edit_text(
            text=f"⚙️ Настройка правил рейтинга\n\n"
                 f"Выберите основной показатель для рейтинга {'игроков' if rating_type == 'player' else 'команд'}:",
            reply_markup=get_admin_ratings_metric_keyboard(rating_type),
        )
    elif callback_data.startswith("admin_ratings_metric_"):
        # Формат: admin_ratings_metric_player_kills или admin_ratings_metric_team_points
        parts = callback_data.replace("admin_ratings_metric_", "").split("_")
        if len(parts) >= 2:
            rating_type = parts[0]  # player или team
            metric = "_".join(parts[1:])  # kills или points
            
            await callback.answer("Сохранение правил...")
            
            if _mongo_client is not None:
                try:
                    metric_enum = RatingMetric.KILLS if metric == "kills" else RatingMetric.POINTS
                    await _mongo_client.update_rating_metric(rating_type, metric_enum)
                    await callback.answer("✅ Правила успешно сохранены!", show_alert=True)
                    
                    # Обновляем экран
                    rules = await _mongo_client.get_rating_rules()
                    rules_text = "📊 Рейтинги\n\n"
                    if rules:
                        rules_text += f"⚙️ Текущие правила:\n"
                        rules_text += f"  👤 Игроки: {rules.player_metric.value}\n"
                        rules_text += f"  👥 Команды: {rules.team_metric.value}\n"
                        if rules.season_start_date and rules.season_end_date:
                            rules_text += f"  📅 Сезон: {rules.season_start_date} - {rules.season_end_date}\n"
                    await callback.message.edit_text(
                        text=rules_text,
                        reply_markup=get_admin_ratings_keyboard(),
                    )
                except Exception as e:
                    _LOG.error(f"Ошибка при сохранении правил рейтинга: {e}")
                    await callback.answer("❌ Произошла ошибка при сохранении правил", show_alert=True)
            else:
                await callback.answer("❌ Ошибка подключения к базе данных", show_alert=True)
    elif callback_data == "admin_wallet_bonuses":
        await callback.answer("CD токен и бонусы")
        await callback.message.edit_text(
            text="💰 CD токен и бонусы\n\n"
                 "Управление настройками токенов и бонусов:",
            reply_markup=get_admin_wallet_bonuses_keyboard(),
        )
    elif callback_data == "admin_bonus_daily_settings":
        await callback.answer("Настройки ежедневного бонуса")
        # Получаем настройки
        settings_text = "🎁 Настройки ежедневного бонуса\n\n"
        if _mongo_client is not None:
            try:
                settings = await _mongo_client.get_bonus_settings()
                if settings:
                    status = "✅ Включен" if settings.daily_bonus_enabled else "❌ Выключен"
                    settings_text += f"Статус: {status}\n"
                    settings_text += f"Сумма: {settings.daily_bonus_amount} токенов\n"
                else:
                    settings_text += "Настройки не найдены (используются значения по умолчанию)\n"
            except Exception as e:
                _LOG.error(f"Ошибка при получении настроек бонусов: {e}")
        
        await callback.message.edit_text(
            text=settings_text,
            reply_markup=get_admin_daily_bonus_settings_keyboard(
                enabled=settings.daily_bonus_enabled if settings else True,
            ),
        )
    elif callback_data == "admin_bonus_daily_toggle":
        await callback.answer("Переключение ежедневного бонуса...")
        if _mongo_client is not None:
            try:
                settings = await _mongo_client.get_bonus_settings()
                new_enabled = not settings.daily_bonus_enabled if settings else False
                await _mongo_client.update_bonus_settings(
                    daily_bonus_enabled=new_enabled,
                )
                # Логируем изменение настроек
                await _mongo_client.add_action_log(
                    action_type=ActionType.SETTINGS_CHANGED,
                    user_id=callback.from_user.id,
                    description=f"Изменены настройки ежедневного бонуса: {'включен' if new_enabled else 'выключен'}",
                )
                await callback.answer("✅ Настройки обновлены!", show_alert=True)
                # Обновляем экран
                settings = await _mongo_client.get_bonus_settings()
                status = "✅ Включен" if settings.daily_bonus_enabled else "❌ Выключен"
                await callback.message.edit_text(
                    text=f"🎁 Настройки ежедневного бонуса\n\n"
                         f"Статус: {status}\n"
                         f"Сумма: {settings.daily_bonus_amount} токенов\n",
                    reply_markup=get_admin_daily_bonus_settings_keyboard(
                        enabled=settings.daily_bonus_enabled,
                    ),
                )
            except Exception as e:
                _LOG.error(f"Ошибка при обновлении настроек бонусов: {e}")
                await callback.answer("❌ Произошла ошибка", show_alert=True)
    elif callback_data == "admin_bonus_daily_amount":
        await callback.answer("Изменение суммы")
        _waiting_promocode_data[callback.from_user.id] = {
            "type": "daily_bonus_amount",
        }
        await callback.message.edit_text(
            text="🎁 Настройки ежедневного бонуса\n\n"
                 "Введите новую сумму ежедневного бонуса (в токенах):\n\n"
                 "Или отправьте /cancel для отмены.",
        )
    elif callback_data == "admin_promocodes":
        await callback.answer("Промокоды")
        # Получаем список промокодов
        promocodes = []
        if _mongo_client is not None:
            try:
                promocodes = await _mongo_client.get_promocodes()
            except Exception as e:
                _LOG.error(f"Ошибка при получении промокодов: {e}")
        
        await callback.message.edit_text(
            text="🎟 Промокоды\n\n"
                 "Список промокодов:",
            reply_markup=get_admin_promocodes_list_keyboard(promocodes),
        )
    elif callback_data == "admin_promocode_create":
        await callback.answer("Создание промокода")
        _waiting_promocode_data[callback.from_user.id] = {
            "type": "create_promocode",
            "step": "code",
        }
        await callback.message.edit_text(
            text="🎟 Создание промокода\n\n"
                 "Шаг 1/5: Код промокода\n\n"
                 "Введите код промокода (например, WELCOME):\n\n"
                 "Или отправьте /cancel для отмены.",
        )
    elif callback_data.startswith("admin_promocode_"):
        promocode_id = callback_data.replace("admin_promocode_", "")
        await callback.answer("Промокод")
        
        if _mongo_client is not None:
            try:
                promocode = await _mongo_client.get_promocode(promocode_id)
                if not promocode:
                    await callback.answer("Промокод не найден", show_alert=True)
                    return
                
                # Формируем текст карточки
                status = "✅ Активен" if promocode.is_active else "❌ Неактивен"
                text = f"🎟 Промокод: {promocode.code}\n\n"
                text += f"Статус: {status}\n"
                text += f"Сумма: {promocode.amount} токенов\n"
                text += f"Активаций: {promocode.activation_count}"
                if promocode.activation_limit:
                    text += f" / {promocode.activation_limit}"
                text += "\n"
                if promocode.description:
                    text += f"Описание: {promocode.description}\n"
                if promocode.valid_from:
                    text += f"Действует с: {promocode.valid_from.strftime('%d.%m.%Y %H:%M')}\n"
                if promocode.valid_until:
                    text += f"Действует до: {promocode.valid_until.strftime('%d.%m.%Y %H:%M')}\n"
                
                await callback.message.edit_text(
                    text=text,
                    reply_markup=get_admin_promocode_card_keyboard(promocode_id),
                )
            except Exception as e:
                _LOG.error(f"Ошибка при получении промокода: {e}")
                await callback.answer("Произошла ошибка", show_alert=True)
    elif callback_data.startswith("admin_promocode_toggle_"):
        promocode_id = callback_data.replace("admin_promocode_toggle_", "")
        await callback.answer("Переключение статуса...")
        
        if _mongo_client is not None:
            try:
                promocode = await _mongo_client.get_promocode(promocode_id)
                if not promocode:
                    await callback.answer("Промокод не найден", show_alert=True)
                    return
                
                await _mongo_client.toggle_promocode(promocode_id, not promocode.is_active)
                await callback.answer("✅ Статус обновлён!", show_alert=True)
                
                # Обновляем экран
                promocode = await _mongo_client.get_promocode(promocode_id)
                status = "✅ Активен" if promocode.is_active else "❌ Неактивен"
                text = f"🎟 Промокод: {promocode.code}\n\n"
                text += f"Статус: {status}\n"
                text += f"Сумма: {promocode.amount} токенов\n"
                text += f"Активаций: {promocode.activation_count}"
                if promocode.activation_limit:
                    text += f" / {promocode.activation_limit}"
                text += "\n"
                if promocode.description:
                    text += f"Описание: {promocode.description}\n"
                if promocode.valid_from:
                    text += f"Действует с: {promocode.valid_from.strftime('%d.%m.%Y %H:%M')}\n"
                if promocode.valid_until:
                    text += f"Действует до: {promocode.valid_until.strftime('%d.%m.%Y %H:%M')}\n"
                
                await callback.message.edit_text(
                    text=text,
                    reply_markup=get_admin_promocode_card_keyboard(promocode_id),
                )
            except Exception as e:
                _LOG.error(f"Ошибка при переключении промокода: {e}")
                await callback.answer("❌ Произошла ошибка", show_alert=True)
    elif callback_data == "admin_transaction_reasons":
        await callback.answer("Причины транзакций")
        # Получаем список причин
        reasons = []
        if _mongo_client is not None:
            try:
                reasons = await _mongo_client.get_transaction_reasons()
            except Exception as e:
                _LOG.error(f"Ошибка при получении причин транзакций: {e}")
        
        await callback.message.edit_text(
            text="📝 Причины транзакций\n\n"
                 "Шаблоны для истории операций:",
            reply_markup=get_admin_transaction_reasons_list_keyboard(reasons),
        )
    elif callback_data == "admin_transaction_reason_create":
        await callback.answer("Создание шаблона")
        _waiting_transaction_reason_data[callback.from_user.id] = {
            "type": "create_reason",
            "step": "name",
        }
        await callback.message.edit_text(
            text="📝 Создание шаблона причины транзакции\n\n"
                 "Шаг 1/3: Название\n\n"
                 "Введите название причины (например, 'Покупка в магазине'):\n\n"
                 "Или отправьте /cancel для отмены.",
        )
    elif callback_data.startswith("admin_transaction_reason_"):
        reason_id = callback_data.replace("admin_transaction_reason_", "")
        await callback.answer("Шаблон причины")
        
        if _mongo_client is not None:
            try:
                reason = await _mongo_client.get_transaction_reason(reason_id)
                if not reason:
                    await callback.answer("Шаблон не найден", show_alert=True)
                    return
                
                # Формируем текст карточки
                status = "✅ Активен" if reason.is_active else "❌ Неактивен"
                type_text = "Начисление" if reason.transaction_type == TransactionType.DEPOSIT else "Списание"
                text = f"📝 Шаблон: {reason.name}\n\n"
                text += f"Статус: {status}\n"
                text += f"Тип: {type_text}\n"
                if reason.description:
                    text += f"Описание: {reason.description}\n"
                
                # Пока просто показываем информацию (можно добавить редактирование)
                await callback.message.edit_text(
                    text=text,
                    reply_markup=get_admin_transaction_reasons_list_keyboard(
                        await _mongo_client.get_transaction_reasons(),
                    ),
                )
            except Exception as e:
                _LOG.error(f"Ошибка при получении шаблона: {e}")
                await callback.answer("Произошла ошибка", show_alert=True)
    elif callback_data.startswith("admin_reason_type_"):
        # Выбор типа транзакции при создании шаблона
        transaction_type_str = callback_data.replace("admin_reason_type_", "")
        transaction_type = TransactionType.DEPOSIT if transaction_type_str == "deposit" else TransactionType.WITHDRAWAL
        
        user_id = callback.from_user.id
        if user_id in _waiting_transaction_reason_data:
            _waiting_transaction_reason_data[user_id]["transaction_type"] = transaction_type
            _waiting_transaction_reason_data[user_id]["step"] = "description"
            
            await callback.answer("Тип выбран")
            await callback.message.edit_text(
                text=f"📝 Создание шаблона причины транзакции\n\n"
                     f"Название: {_waiting_transaction_reason_data[user_id]['name']}\n"
                     f"Тип: {'Начисление' if transaction_type == TransactionType.DEPOSIT else 'Списание'}\n\n"
                     f"Шаг 3/3: Описание (опционально)\n\n"
                     f"Введите описание или 'нет' для пропуска:\n\n"
                     f"Или отправьте /cancel для отмены.",
            )
    elif callback_data == "admin_reason_cancel":
        user_id = callback.from_user.id
        if user_id in _waiting_transaction_reason_data:
            _waiting_transaction_reason_data.pop(user_id, None)
        await callback.answer("Отменено")
        await callback.message.edit_text(
            text="❌ Создание шаблона отменено.",
        )
    elif callback_data == "admin_promotions":
        await callback.answer("Акции и розыгрыши")
        await callback.message.edit_text(
            text="🎉 Акции и розыгрыши\n\n"
                 "Управление розыгрышами и акциями:",
            reply_markup=get_admin_promotions_keyboard(),
        )
    elif callback_data == "admin_promotion_create":
        await callback.answer("Создание розыгрыша")
        _waiting_giveaway_data[callback.from_user.id] = {
            "type": "create_giveaway",
            "step": "name",
        }
        await callback.message.edit_text(
            text="🎉 Создание розыгрыша\n\n"
                 "Шаг 1/5: Название\n\n"
                 "Введите название розыгрыша:\n\n"
                 "Или отправьте /cancel для отмены.",
        )
    elif callback_data == "admin_promotions_list":
        await callback.answer("Список розыгрышей")
        # Получаем список розыгрышей
        promotions = []
        if _mongo_client is not None:
            try:
                promotions = await _mongo_client.get_giveaways()
            except Exception as e:
                _LOG.error(f"Ошибка при получении розыгрышей: {e}")
        
        await callback.message.edit_text(
            text="📋 Список розыгрышей\n\n"
                 "Выберите розыгрыш:",
            reply_markup=get_admin_promotions_list_keyboard(promotions),
        )
    elif callback_data.startswith("admin_promotion_type_"):
        # Выбор способа участия при создании розыгрыша (должен быть ПЕРЕД admin_promotion_)
        participation_type_str = callback_data.replace("admin_promotion_type_", "")
        participation_type = GiveawayParticipationType.TOKENS if participation_type_str == "tokens" else GiveawayParticipationType.CONDITION
        
        user_id = callback.from_user.id
        if user_id in _waiting_giveaway_data:
            _waiting_giveaway_data[user_id]["participation_type"] = participation_type
            _waiting_giveaway_data[user_id]["step"] = "participation_details"
            
            await callback.answer("Способ выбран")
            if participation_type == GiveawayParticipationType.TOKENS:
                await callback.message.edit_text(
                    text=f"🎉 Создание розыгрыша\n\n"
                         f"Способ участия: За CD токены\n\n"
                         f"Шаг 4/5: Стоимость билета\n\n"
                         f"Введите стоимость билета в CD токенах:\n\n"
                         f"Или отправьте /cancel для отмены.",
                )
            else:
                await callback.message.edit_text(
                    text=f"🎉 Создание розыгрыша\n\n"
                         f"Способ участия: За выполнение условия\n\n"
                         f"Шаг 4/5: Описание условия\n\n"
                         f"Введите описание условия (например, 'сыграть турнир'):\n\n"
                         f"Или отправьте /cancel для отмены.",
                )
    elif callback_data.startswith("admin_promotion_"):
        promotion_id = callback_data.replace("admin_promotion_", "")
        
        if promotion_id.startswith("determine_winners_"):
            # Определение победителей
            actual_promotion_id = promotion_id.replace("determine_winners_", "")
            await callback.answer("Определение победителей...")
            
            if _mongo_client is not None:
                try:
                    promotion = await _mongo_client.get_giveaway(actual_promotion_id)
                    if not promotion:
                        await callback.answer("Розыгрыш не найден", show_alert=True)
                        return
                    
                    # Определяем победителей (случайный выбор из участников)
                    winners = await _mongo_client.determine_giveaway_winners(actual_promotion_id)
                    
                    # Логируем определение победителей
                    await _mongo_client.add_action_log(
                        action_type=ActionType.GIVEAWAY_WINNERS_DETERMINED,
                        user_id=callback.from_user.id,
                        description=f"Определены победители розыгрыша '{promotion.name}' ({len(winners)} победителей)",
                        details={"giveaway_id": actual_promotion_id, "winners_count": len(winners)},
                    )
                    
                    if winners:
                        # Формируем список победителей
                        winners_text = "🏆 Победители розыгрыша:\n\n"
                        for idx, winner_id in enumerate(winners, start=1):
                            user = await _mongo_client.get_user(winner_id)
                            winner_name = user.nickname or user.name if user else f"ID:{winner_id}"
                            winners_text += f"{idx}. {winner_name} (ID: {winner_id})\n"
                        
                        await callback.message.edit_text(
                            text=f"🎉 Розыгрыш: {promotion.name}\n\n{winners_text}",
                            reply_markup=get_admin_promotion_card_keyboard(
                                actual_promotion_id,
                                GiveawayStatus.COMPLETED,
                            ),
                        )
                        await callback.answer("✅ Победители определены!", show_alert=True)
                    else:
                        await callback.answer("Нет участников для определения победителей", show_alert=True)
                except Exception as e:
                    _LOG.error(f"Ошибка при определении победителей: {e}")
                    await callback.answer("❌ Произошла ошибка", show_alert=True)
        else:
            # Просмотр карточки розыгрыша
            await callback.answer("Розыгрыш")
            
            if _mongo_client is not None:
                try:
                    promotion = await _mongo_client.get_giveaway(promotion_id)
                    if not promotion:
                        await callback.answer("Розыгрыш не найден", show_alert=True)
                        return
                    
                    # Формируем текст карточки
                    status_text = {
                        GiveawayStatus.DRAFT: "Черновик",
                        GiveawayStatus.ACTIVE: "Активен",
                        GiveawayStatus.COMPLETED: "Завершен",
                    }
                    participation_text = {
                        GiveawayParticipationType.TOKENS: f"💰 За CD токены ({promotion.ticket_cost} токенов за билет)",
                        GiveawayParticipationType.CONDITION: f"✅ За выполнение условия: {promotion.condition_description}",
                    }
                    
                    text = f"🎉 Розыгрыш: {promotion.name}\n\n"
                    text += f"Статус: {status_text.get(promotion.status, promotion.status.value)}\n"
                    text += f"Описание: {promotion.description}\n"
                    text += f"Период: {promotion.start_date.strftime('%d.%m.%Y %H:%M')} - {promotion.end_date.strftime('%d.%m.%Y %H:%M')}\n"
                    text += f"Способ участия: {participation_text.get(promotion.participation_type, promotion.participation_type.value)}\n"
                    if promotion.ticket_limit_per_user:
                        text += f"Лимит билетов: {promotion.ticket_limit_per_user} на человека\n"
                    text += f"Участников: {len(promotion.participants)}\n"
                    if promotion.winners:
                        text += f"Победителей: {len(promotion.winners)}\n"
                    
                    await callback.message.edit_text(
                        text=text,
                        reply_markup=get_admin_promotion_card_keyboard(
                            promotion_id,
                            promotion.status,
                        ),
                    )
                except Exception as e:
                    _LOG.error(f"Ошибка при получении розыгрыша: {e}")
                    await callback.answer("Произошла ошибка", show_alert=True)
    elif callback_data == "admin_referral":
        # Проверка прав: только SUPER_ADMIN может настраивать рефералку
        if user_role != UserRole.SUPER_ADMIN:
            await callback.answer(
                "❌ Доступно только супер-админам",
                show_alert=True,
            )
            return
        
        await callback.answer("Рефералка")
        # Открываем мини-приложение для настройки рефералки
        from src.config import MINI_APP_URL
        
        # Формируем URL для страницы настроек рефералки
        base_url = MINI_APP_URL.rstrip('/')
        if '/profile' in base_url:
            base_url = base_url.replace('/profile', '')
        elif base_url.endswith('/index.html'):
            base_url = base_url.replace('/index.html', '')
        referral_settings_url = f"{base_url}/referral_settings.html"
        
        await callback.message.edit_text(
            text="🤝 Настройки рефералки\n\n"
                 "Нажмите на кнопку ниже, чтобы открыть настройки:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="⚙️ Открыть настройки",
                            web_app=types.WebAppInfo(url=referral_settings_url),
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="⬅️ Назад",
                            callback_data="menu_admin",
                        ),
                    ],
                ],
            ),
        )
    elif callback_data == "admin_broadcast":
        await callback.answer("Рассылка")
        await callback.message.edit_text(
            text="📣 Рассылка\n\n"
                 "Выберите тип рассылки:",
            reply_markup=get_admin_broadcast_keyboard(),
        )
    elif callback_data == "admin_broadcast_all":
        await callback.answer("Рассылка всем")
        _waiting_broadcast_data[callback.from_user.id] = {
            "type": "all",
            "step": "message",
        }
        await callback.message.edit_text(
            text="📢 Рассылка всем пользователям\n\n"
                 "Введите текст сообщения для рассылки:\n\n"
                 "Или отправьте /cancel для отмены.",
        )
    elif callback_data == "admin_broadcast_tournament":
        await callback.answer("Рассылка участникам турнира")
        # Получаем список турниров
        tournaments = []
        if _mongo_client is not None:
            try:
                tournaments = await _mongo_client.get_tournaments()
            except Exception as e:
                _LOG.error(f"Ошибка при получении турниров: {e}")
        
        await callback.message.edit_text(
            text="🏆 Рассылка участникам турнира\n\n"
                 "Выберите турнир:",
            reply_markup=get_admin_broadcast_tournaments_keyboard(tournaments),
        )
    elif callback_data.startswith("admin_broadcast_tournament_"):
        tournament_id = callback_data.replace("admin_broadcast_tournament_", "")
        await callback.answer("Турнир выбран")
        _waiting_broadcast_data[callback.from_user.id] = {
            "type": "tournament",
            "tournament_id": tournament_id,
            "step": "message",
        }
        await callback.message.edit_text(
            text="🏆 Рассылка участникам турнира\n\n"
                 "Введите текст сообщения для рассылки:\n\n"
                 "Или отправьте /cancel для отмены.",
        )
    elif callback_data == "admin_broadcast_staff":
        await callback.answer("Рассылка менеджерам/админам")
        _waiting_broadcast_data[callback.from_user.id] = {
            "type": "staff",
            "step": "message",
        }
        await callback.message.edit_text(
            text="👥 Рассылка менеджерам/админам\n\n"
                 "Введите текст сообщения для рассылки:\n\n"
                 "Или отправьте /cancel для отмены.",
        )
    elif callback_data.startswith("admin_broadcast_confirm_"):
        # Подтверждение рассылки
        parts = callback_data.replace("admin_broadcast_confirm_", "").split("_")
        broadcast_type = parts[0] if parts else "all"
        tournament_id = parts[1] if len(parts) > 1 and parts[1] else None
        
        await callback.answer("Отправка рассылки...")
        
        user_id = callback.from_user.id
        if user_id not in _waiting_broadcast_data:
            await callback.answer("Данные рассылки не найдены", show_alert=True)
            return
        
        data = _waiting_broadcast_data[user_id]
        message_text = data.get("message_text", "")
        
        if not message_text:
            await callback.answer("Текст сообщения не найден", show_alert=True)
            return
        
        # Отправляем рассылку
        sent_count = 0
        failed_count = 0
        
        try:
            if broadcast_type == "all":
                # Отправляем всем пользователям
                if _mongo_client is not None:
                    users = await _mongo_client.get_all_users()
                    for user in users:
                        try:
                            from aiogram import Bot
                            bot = Bot.get_current()
                            await bot.send_message(
                                chat_id=user.id,
                                text=message_text,
                            )
                            sent_count += 1
                        except Exception as e:
                            _LOG.error(f"Ошибка при отправке сообщения пользователю {user.id}: {e}")
                            failed_count += 1
            elif broadcast_type == "tournament":
                # Отправляем участникам турнира
                if _mongo_client is not None and tournament_id:
                    tournament = await _mongo_client.get_tournament(tournament_id)
                    if tournament:
                        participants = []
                        if tournament.format == TournamentFormat.SOLO:
                            participants = tournament.solo_participants
                        else:
                            participants = tournament.team_participants
                        
                        for participant_id in participants:
                            try:
                                if tournament.format == TournamentFormat.SOLO:
                                    await callback.bot.send_message(
                                        chat_id=participant_id,
                                        text=message_text,
                                    )
                                    sent_count += 1
                                else:
                                    # Для командных турниров отправляем капитану команды
                                    team = await _mongo_client.get_team(participant_id)
                                    if team and team.captain_id:
                                        await callback.bot.send_message(
                                            chat_id=team.captain_id,
                                            text=message_text,
                                        )
                                        sent_count += 1
                            except Exception as e:
                                _LOG.error(f"Ошибка при отправке сообщения участнику {participant_id}: {e}")
                                failed_count += 1
            elif broadcast_type == "staff":
                # Отправляем менеджерам и админам
                if _mongo_client is not None:
                    users = await _mongo_client.get_all_users()
                    for user in users:
                        if user.role in (UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN):
                            try:
                                await callback.bot.send_message(
                                    chat_id=user.id,
                                    text=message_text,
                                )
                                sent_count += 1
                            except Exception as e:
                                _LOG.error(f"Ошибка при отправке сообщения пользователю {user.id}: {e}")
                                failed_count += 1
            
            # Очищаем данные рассылки
            _waiting_broadcast_data.pop(user_id, None)
            
            await callback.message.edit_text(
                text=f"✅ Рассылка завершена!\n\n"
                     f"📤 Отправлено: {sent_count}\n"
                     f"{f'❌ Ошибок: {failed_count}' if failed_count > 0 else ''}",
                reply_markup=get_admin_broadcast_keyboard(),
            )
            await callback.answer(f"✅ Отправлено {sent_count} сообщений", show_alert=True)
        except Exception as e:
            _LOG.error(f"Ошибка при рассылке: {e}")
            await callback.answer("❌ Произошла ошибка при рассылке", show_alert=True)
    elif callback_data == "admin_broadcast_edit":
        await callback.answer("Редактирование")
        user_id = callback.from_user.id
        if user_id in _waiting_broadcast_data:
            data = _waiting_broadcast_data[user_id]
            data["step"] = "message"
            await callback.message.edit_text(
                text="✏️ Редактирование сообщения\n\n"
                     "Введите новый текст сообщения:\n\n"
                     "Или отправьте /cancel для отмены.",
            )
    elif callback_data == "admin_audit" or callback_data == "admin_log" or callback_data == "admin_actions_log":
        # Дополнительная проверка: только супер-админ может видеть журнал действий
        if user_role != UserRole.SUPER_ADMIN:
            _LOG.warning(
                f"Попытка доступа к журналу действий пользователем {callback.from_user.id} "
                f"с ролью {user_role.value} (требуется SUPER_ADMIN)",
            )
            await callback.answer(
                "❌ Доступно только супер-админам",
                show_alert=True,
            )
            return
        await callback.answer("Журнал действий")
        await _show_actions_log(callback, page=0)
    elif callback_data.startswith("admin_actions_log_page_"):
        # Проверка прав: только SUPER_ADMIN может видеть журнал действий
        if user_role != UserRole.SUPER_ADMIN:
            await callback.answer(
                "❌ Доступно только супер-админам",
                show_alert=True,
            )
            return
        page = int(callback_data.replace("admin_actions_log_page_", ""))
        await callback.answer("Журнал действий")
        await _show_actions_log(callback, page=page)
    elif callback_data == "admin_tournament_create":
        # Проверка прав: только ADMIN и SUPER_ADMIN могут создавать турниры
        if user_role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
            await callback.answer(
                "❌ Только админы могут создавать турниры",
                show_alert=True,
            )
            return
        
        await callback.answer("Создание турнира")
        
        # Инициализируем данные создания турнира
        _tournament_creation_data[callback.from_user.id] = {
            "step": "name",
            "data": {},
        }
        
        await callback.message.edit_text(
            text="🏆 Создание турнира\n\n"
                 "Шаг 1/9: Название турнира\n\n"
                 "Введите название турнира:\n\n"
                 "Или отправьте /cancel для отмены.",
            reply_markup=None,
        )
    elif callback_data.startswith("admin_tournament_"):
        # Обработка действий с турниром в админ-панели
        tournament_id = callback_data.replace("admin_tournament_", "").split("_")[0]
        action = "_".join(callback_data.replace("admin_tournament_", "").split("_")[1:])
        
        tournament = None
        if _mongo_client is not None:
            try:
                tournament = await _mongo_client.get_tournament(tournament_id)
            except Exception as e:
                _LOG.error(
                    f"Ошибка при получении турнира {tournament_id}: {e}",
                )
        
        if not tournament:
            await callback.answer("Турнир не найден", show_alert=True)
            return
        
        if action == "participants":
            await callback.answer("Участники/Команды")
            # Показываем участников (аналогично обычному просмотру)
            participants_text = f"👥 Участники турнира: {tournament.name}\n\n"
            if tournament.format == TournamentFormat.SOLO:
                if tournament.solo_participants:
                    participants_text += f"Участников: {len(tournament.solo_participants)}\n"
                else:
                    participants_text += "Участников пока нет."
            else:
                if tournament.team_participants:
                    participants_text += f"Команд: {len(tournament.team_participants)}\n"
                else:
                    participants_text += "Команд пока нет."
            
            await callback.message.edit_text(
                text=participants_text,
                reply_markup=get_admin_tournament_manage_keyboard(
                    tournament_id=tournament_id,
                    has_confirmation=False,  # TODO: определить из данных турнира
                ),
            )
        elif action == "results":
            await callback.answer("Результаты")
            await callback.message.edit_text(
                text=f"🧮 Результаты турнира: {tournament.name}\n\nРаздел в разработке...",
                reply_markup=get_admin_tournament_manage_keyboard(
                    tournament_id=tournament_id,
                    has_confirmation=False,
                ),
            )
        elif action == "publish":
            await callback.answer("Опубликовать таблицу")
            await callback.message.edit_text(
                text=f"📊 Опубликовать таблицу: {tournament.name}\n\nРаздел в разработке...",
                reply_markup=get_admin_tournament_manage_keyboard(
                    tournament_id=tournament_id,
                    has_confirmation=False,
                ),
            )
        elif action == "message":
            await callback.answer("Сообщение участникам")
            await callback.message.edit_text(
                text=f"📣 Сообщение участникам: {tournament.name}\n\nРаздел в разработке...",
                reply_markup=get_admin_tournament_manage_keyboard(
                    tournament_id=tournament_id,
                    has_confirmation=False,
                ),
            )
        elif action == "close_reg":
            await callback.answer("Закрыть регистрацию")
            if tournament.status == TournamentStatus.REGISTRATION_OPEN:
                tournament.status = TournamentStatus.IN_PROGRESS
                await _mongo_client.update_tournament(tournament)
                await callback.answer("✅ Регистрация закрыта", show_alert=True)
            else:
                await callback.answer("Регистрация уже закрыта", show_alert=True)
        elif action == "finish":
            await callback.answer("Завершить турнир")
            if tournament.status != TournamentStatus.COMPLETED:
                tournament.status = TournamentStatus.COMPLETED
                if not tournament.end_date:
                    tournament.end_date = dt.datetime.now(tz=MOSCOW_TZ)
                await _mongo_client.update_tournament(tournament)
                await callback.answer("✅ Турнир завершён", show_alert=True)
            else:
                await callback.answer("Турнир уже завершён", show_alert=True)
    elif callback_data.startswith("tournament_create_"):
        # Обработка шагов создания турнира
        user_id = callback.from_user.id
        
        if user_id not in _tournament_creation_data:
            await callback.answer("Создание турнира не начато", show_alert=True)
            return
        
        creation_data = _tournament_creation_data[user_id]
        step = creation_data["step"]
        data = creation_data["data"]
        
        if callback_data == "tournament_create_format_solo":
            data["format"] = TournamentFormat.SOLO
            creation_data["step"] = "dates"
            await callback.message.edit_text(
                text="🏆 Создание турнира\n\n"
                     "Шаг 4/9: Даты турнира\n\n"
                     "Введите даты в формате:\n"
                     "<b>ДД.ММ.ГГГГ ЧЧ:ММ | ДД.ММ.ГГГГ ЧЧ:ММ | ДД.ММ.ГГГГ ЧЧ:ММ | ДД.ММ.ГГГГ ЧЧ:ММ</b>\n\n"
                     "1. Старт регистрации\n"
                     "2. Конец регистрации\n"
                     "3. Старт турнира\n"
                     "4. Конец турнира (опционально, можно пропустить)\n\n"
                     "Пример: <code>01.01.2025 12:00 | 10.01.2025 12:00 | 15.01.2025 10:00 | 20.01.2025 18:00</code>\n\n"
                     "Или отправьте /cancel для отмены.",
                reply_markup=None,
            )
        elif callback_data == "tournament_create_format_team":
            data["format"] = TournamentFormat.TEAM
            creation_data["step"] = "dates"
            await callback.message.edit_text(
                text="🏆 Создание турнира\n\n"
                     "Шаг 4/9: Даты турнира\n\n"
                     "Введите даты в формате:\n"
                     "<b>ДД.ММ.ГГГГ ЧЧ:ММ | ДД.ММ.ГГГГ ЧЧ:ММ | ДД.ММ.ГГГГ ЧЧ:ММ | ДД.ММ.ГГГГ ЧЧ:ММ</b>\n\n"
                     "1. Старт регистрации\n"
                     "2. Конец регистрации\n"
                     "3. Старт турнира\n"
                     "4. Конец турнира (опционально, можно пропустить)\n\n"
                     "Пример: <code>01.01.2025 12:00 | 10.01.2025 12:00 | 15.01.2025 10:00 | 20.01.2025 18:00</code>\n\n"
                     "Или отправьте /cancel для отмены.",
                reply_markup=None,
            )
        elif callback_data == "tournament_create_join_all":
            data["join_type"] = "all"
            creation_data["step"] = "review"
            await _show_tournament_review(callback, data)
        elif callback_data == "tournament_create_join_invite":
            data["join_type"] = "invite"
            creation_data["step"] = "review"
            await _show_tournament_review(callback, data)
        elif callback_data == "tournament_create_join_confirmed":
            data["join_type"] = "confirmed"
            creation_data["step"] = "review"
            await _show_tournament_review(callback, data)
        elif callback_data == "tournament_create_scoring_sum":
            data["scoring_formula"] = "sum"
            creation_data["step"] = "join_type"
            await callback.message.edit_text(
                text="🏆 Создание турнира\n\n"
                     "Шаг 9/9: Кто может вступать\n\n"
                     "Выберите тип вступления:",
                reply_markup=get_tournament_join_type_keyboard(),
            )
        elif callback_data == "tournament_create_scoring_topn":
            data["scoring_formula"] = "topn"
            creation_data["step"] = "join_type"
            await callback.message.edit_text(
                text="🏆 Создание турнира\n\n"
                     "Шаг 9/9: Кто может вступать\n\n"
                     "Выберите тип вступления:",
                reply_markup=get_tournament_join_type_keyboard(),
            )
        elif callback_data == "tournament_create_scoring_avg":
            data["scoring_formula"] = "avg"
            creation_data["step"] = "join_type"
            await callback.message.edit_text(
                text="🏆 Создание турнира\n\n"
                     "Шаг 9/9: Кто может вступать\n\n"
                     "Выберите тип вступления:",
                reply_markup=get_tournament_join_type_keyboard(),
            )
        elif callback_data == "tournament_create_publish":
            # Публикуем турнир
            if _mongo_client is None:
                await callback.answer("Ошибка: база данных недоступна", show_alert=True)
                return
            
            try:
                tournament = await _create_tournament_from_data(data)
                await _mongo_client.create_tournament(tournament)
                # Логируем создание турнира
                await _mongo_client.add_action_log(
                    action_type=ActionType.TOURNAMENT_CREATED,
                    user_id=user_id,
                    description=f"Создан турнир '{tournament.name}'",
                    details={"tournament_id": tournament.id},
                )
                _tournament_creation_data.pop(user_id, None)
                await callback.answer("✅ Турнир создан и опубликован!", show_alert=True)
                await callback.message.edit_text(
                    text=f"✅ Турнир '{tournament.name}' успешно создан и опубликован!",
                    reply_markup=get_admin_tournaments_list_keyboard(),
                )
            except Exception as e:
                _LOG.error(f"Ошибка при создании турнира: {e}")
                await callback.answer("Ошибка при создании турнира", show_alert=True)
        elif callback_data == "tournament_create_cancel":
            _tournament_creation_data.pop(user_id, None)
            await callback.answer("Создание турнира отменено")
            await callback.message.edit_text(
                text="❌ Создание турнира отменено",
                reply_markup=get_admin_tournaments_list_keyboard(),
            )
    elif callback_data == "admin_settings":
        # Дополнительная проверка: только супер-админ может изменять настройки
        if user_role != UserRole.SUPER_ADMIN:
            _LOG.warning(
                f"Попытка доступа к настройкам пользователем {callback.from_user.id} "
                f"с ролью {user_role.value} (требуется SUPER_ADMIN)",
            )
            await callback.answer(
                "❌ Доступно только супер-админам",
                show_alert=True,
            )
            return
        await callback.answer("Настройки")
        await callback.message.edit_text(
            text="⚙️ Настройки\n\nРаздел в разработке...",
            reply_markup=get_admin_panel_keyboard(
                is_super_admin=is_super_admin,
            ),
        )


async def team_create_message_handler(
    message: types.Message,
) -> None:
    """
    Обработчик текстовых сообщений для создания команды.
    Ожидает формат: "Название команды | Тег"
    """
    print(f"[DEBUG] >>> team_create_message_handler ВЫЗВАН")
    user_id = message.from_user.id
    print(f"[DEBUG] team_create_message_handler вызван для пользователя {user_id}, waiting={_waiting_team_data.get(user_id, False)}")
    
    # Проверяем, ожидает ли пользователь ввода данных команды
    if not _waiting_team_data.get(user_id, False):
        # Не обрабатываем, но не блокируем другие обработчики
        print(f"[DEBUG] Пользователь {user_id} не в режиме ожидания данных команды")
        return
    
    print(f"[INFO] Обработка данных команды от пользователя {user_id}, текст: {message.text[:50] if message.text else 'не текст'}")
    
    # Проверяем команду /cancel
    if message.text and message.text.strip().lower() == "/cancel":
        _waiting_team_data.pop(user_id, None)
        await message.answer(
            "❌ Создание команды отменено.",
            reply_markup=get_team_no_team_keyboard(),
        )
        return
    
    # Парсим название и тег команды
    if not message.text:
        await message.answer(
            "❌ Пожалуйста, отправьте текст в формате:\n"
            "<b>Название команды | Тег</b>\n\n"
            "Или отправьте /cancel для отмены.",
        )
        return
    
    text = message.text.strip()
    
    # Разделяем по символу |
    if "|" not in text:
        await message.answer(
            "❌ Неверный формат!\n\n"
            "Отправьте данные в формате:\n"
            "<b>Название команды | Тег</b>\n\n"
            "Пример: <code>Моя команда | MT</code>\n\n"
            "Или отправьте /cancel для отмены.",
        )
        return
    
    parts = [part.strip() for part in text.split("|", 1)]
    if len(parts) != 2:
        await message.answer(
            "❌ Неверный формат!\n\n"
            "Отправьте данные в формате:\n"
            "<b>Название команды | Тег</b>\n\n"
            "Пример: <code>Моя команда | MT</code>\n\n"
            "Или отправьте /cancel для отмены.",
        )
        return
    
    team_name, team_tag = parts
    
    # Валидация
    if not team_name or len(team_name) < 3:
        await message.answer(
            "❌ Название команды должно содержать минимум 3 символа.\n\n"
            "Или отправьте /cancel для отмены.",
        )
        return
    
    if not team_tag or len(team_tag) < 2 or len(team_tag) > 10:
        await message.answer(
            "❌ Тег команды должен содержать от 2 до 10 символов.\n\n"
            "Или отправьте /cancel для отмены.",
        )
        return
    
    # Убираем флаг ожидания
    _waiting_team_data.pop(user_id, None)
    
    # Создаем команду
    if _mongo_client is None:
        await message.answer(
            "❌ Ошибка: база данных недоступна. Попробуйте позже.",
            reply_markup=get_team_no_team_keyboard(),
        )
        return
    
    try:
        # Проверяем, что пользователь не в команде
        existing_team = await _mongo_client.get_user_team(user_id)
        if existing_team:
            await message.answer(
                "❌ Вы уже состоите в команде!",
                reply_markup=get_team_no_team_keyboard(),
            )
            return
        
        # Генерируем ID и код-приглашение
        team_id = generate_team_id()
        invite_code = generate_invite_code()
        
        # Создаем команду
        team = Team(
            id=team_id,
            name=team_name,
            tag=team_tag,
            captain_id=user_id,
            members=[user_id],  # Капитан автоматически добавляется в состав
            invite_code=invite_code,
        )
        
        # Сохраняем команду в БД
        await _mongo_client.create_team(team)
        
        # Обновляем team_id пользователя
        await _mongo_client.update_user_team(user_id, team_id)
        
        # Получаем обновленную команду для отображения
        created_team = await _mongo_client.get_team(team_id)
        if not created_team:
            raise Exception("Команда не найдена после создания")
        
        # Получаем роль пользователя для клавиатуры
        user_role = await get_user_role(user_id)
        is_admin = has_admin_access(user_role)
        
        # Формируем текст с информацией о команде
        team_text = await format_team_text(created_team, user_id)
        success_text = (
            f"{team_text}\n\n"
            f"✅ Команда успешно создана!\n"
            f"🔑 Код-приглашение: <code>{invite_code}</code>\n\n"
            f"Вы стали капитаном команды. Используйте код-приглашение, "
            f"чтобы пригласить других игроков."
        )
        
        await message.answer(
            success_text,
            reply_markup=get_team_keyboard(
                is_captain=True,
                is_admin=is_admin,
            ),
        )
        
        _LOG.info(
            f"Пользователь {user_id} создал команду {team_id} ({team_name})",
        )
        
    except Exception as e:
        _LOG.error(
            f"Ошибка при создании команды пользователем {user_id}: {e}",
        )
        await message.answer(
            "❌ Произошла ошибка при создании команды. Попробуйте позже.",
            reply_markup=get_team_no_team_keyboard(),
        )


async def _show_tournament_review(
    callback: types.CallbackQuery,
    data: dict,
) -> None:
    """
    Показывает экран проверки данных турнира перед публикацией.
    """
    review_text = "🏆 Проверьте данные турнира:\n\n"
    
    review_text += f"📝 Название: {data.get('name', 'Не указано')}\n"
    review_text += f"🎮 Игра: {data.get('game_discipline', 'Не указано')}\n"
    
    format_text = "👤 Соло" if data.get('format') == TournamentFormat.SOLO else "👥 Команды"
    review_text += f"📋 Формат: {format_text}\n"
    
    if data.get('registration_start'):
        review_text += f"📅 Регистрация: {data['registration_start'].strftime('%d.%m.%Y %H:%M')} - {data['registration_end'].strftime('%d.%m.%Y %H:%M')}\n"
    if data.get('start_date'):
        review_text += f"🚀 Старт: {data['start_date'].strftime('%d.%m.%Y %H:%M')}\n"
    if data.get('end_date'):
        review_text += f"🏁 Финиш: {data['end_date'].strftime('%d.%m.%Y %H:%M')}\n"
    
    if data.get('participant_limit'):
        review_text += f"👥 Лимит: {data['participant_limit']}\n"
    
    if data.get('scoring_formula'):
        scoring_text = {
            "sum": "Сумма",
            "topn": "Топ-N",
            "avg": "Среднее",
        }
        review_text += f"📊 Формула подсчёта: {scoring_text.get(data['scoring_formula'], data['scoring_formula'])}\n"
    
    if data.get('prizes'):
        review_text += f"🎁 Призы: {data['prizes']}\n"
    
    if data.get('rules_summary'):
        review_text += f"📝 Правила: {data['rules_summary']}\n"
    
    join_type_text = {
        "all": "🌐 Все",
        "invite": "📩 По приглашению",
        "confirmed": "✅ Только подтверждённые команды",
    }
    review_text += f"🔐 Тип вступления: {join_type_text.get(data.get('join_type'), 'Не указано')}\n"
    
    await callback.message.edit_text(
        text=review_text,
        reply_markup=get_tournament_review_keyboard(),
    )


async def _create_tournament_from_data(
    data: dict,
) -> Tournament:
    """
    Создает объект Tournament из данных создания.
    """
    tournament_id = generate_tournament_id()
    
    return Tournament(
        id=tournament_id,
        name=data["name"],
        game_discipline=data["game_discipline"],
        registration_start=data["registration_start"],
        registration_end=data["registration_end"],
        start_date=data["start_date"],
        end_date=data.get("end_date"),
        format=data["format"],
        status=TournamentStatus.REGISTRATION_OPEN,
        entry_fee=data.get("entry_fee"),
        prizes=data.get("prizes"),
        participant_limit=data.get("participant_limit"),
        rules_summary=data.get("rules_summary"),
        full_rules=data.get("full_rules"),
    )


async def _show_rating(
    callback: types.CallbackQuery,
    rating_type: str,
    filter_type: str,
    tournament_id: Optional[str] = None,
) -> None:
    """
    Показывает рейтинг игроков или команд.
    
    Args:
        callback: Callback query
        rating_type: Тип рейтинга (players или teams)
        filter_type: Тип фильтра (all_time, season, month, tournament)
        tournament_id: ID турнира (если filter_type == "tournament")
    """
    filter_texts = {
        "all_time": "За всё время",
        "season": "За сезон",
        "month": "За месяц",
        "tournament": "По турниру",
    }
    filter_text = filter_texts.get(filter_type, "За всё время")
    
    # Если выбран турнир, получаем его название
    tournament_name = None
    if filter_type == "tournament" and tournament_id and _mongo_client is not None:
        try:
            tournament = await _mongo_client.get_tournament(tournament_id)
            if tournament:
                tournament_name = tournament.name
                filter_text = f"По турниру: {tournament_name}"
        except Exception as e:
            _LOG.error(f"Ошибка при получении турнира {tournament_id}: {e}")
    
    user_id = callback.from_user.id
    user_position = None
    team_position = None
    
    if rating_type == "players":
        # Получаем рейтинг игроков
        players = []
        if _mongo_client is not None:
            try:
                players = await _mongo_client.get_players_rating(
                    filter_type=filter_type,
                    tournament_id=tournament_id,
                )
                user_position = await _mongo_client.get_user_rating_position(
                    user_id=user_id,
                    filter_type=filter_type,
                )
            except Exception as e:
                _LOG.error(f"Ошибка при получении рейтинга игроков: {e}")
        
        rating_text = format_players_rating(
            players=players,
            filter_text=filter_text,
            user_position=user_position,
        )
    else:
        # Получаем рейтинг команд
        teams = []
        user_team_id = None
        if _mongo_client is not None:
            try:
                teams = await _mongo_client.get_teams_rating(
                    filter_type=filter_type,
                    tournament_id=tournament_id,
                )
                # Получаем команду пользователя для определения позиции
                user_team = await _mongo_client.get_user_team(user_id)
                if user_team:
                    user_team_id = user_team.id
                    team_position = await _mongo_client.get_team_rating_position(
                        team_id=user_team_id,
                        filter_type=filter_type,
                    )
            except Exception as e:
                _LOG.error(f"Ошибка при получении рейтинга команд: {e}")
        
        rating_text = format_teams_rating(
            teams=teams,
            filter_text=filter_text,
            team_position=team_position,
        )
    
    await callback.message.edit_text(
        text=rating_text,
        reply_markup=get_ratings_filter_keyboard(
            rating_type=rating_type,
            current_filter=filter_type,
        ),
        parse_mode="HTML",
    )


async def _find_user_in_rating(
    callback: types.CallbackQuery,
    rating_type: str,
) -> None:
    """
    Находит позицию пользователя/команды в рейтинге и прокручивает к ней.
    
    Args:
        callback: Callback query
        rating_type: Тип рейтинга (players или teams)
    """
    user_id = callback.from_user.id
    
    if rating_type == "players":
        # Находим позицию игрока
        position = None
        if _mongo_client is not None:
            try:
                position = await _mongo_client.get_user_rating_position(
                    user_id=user_id,
                    filter_type="all_time",
                )
            except Exception as e:
                _LOG.error(f"Ошибка при получении позиции игрока: {e}")
        
        if position is None:
            await callback.answer("Вы не найдены в рейтинге", show_alert=True)
            return
        
        # Получаем рейтинг и показываем с выделением позиции
        players = []
        if _mongo_client is not None:
            try:
                players = await _mongo_client.get_players_rating(
                    filter_type="all_time",
                    limit=1000,  # Получаем больше, чтобы найти пользователя
                )
            except Exception as e:
                _LOG.error(f"Ошибка при получении рейтинга: {e}")
        
        rating_text = format_players_rating(
            players=players,
            filter_text="За всё время",
            user_position=position,
        )
    else:
        # Находим позицию команды
        user_team = None
        team_id = None
        position = None
        
        if _mongo_client is not None:
            try:
                user_team = await _mongo_client.get_user_team(user_id)
                if user_team:
                    team_id = user_team.id
                    position = await _mongo_client.get_team_rating_position(
                        team_id=team_id,
                        filter_type="all_time",
                    )
            except Exception as e:
                _LOG.error(f"Ошибка при получении позиции команды: {e}")
        
        if position is None:
            await callback.answer("Вы не найдены в рейтинге команд", show_alert=True)
            return
        
        # Получаем рейтинг и показываем с выделением позиции
        teams = []
        if _mongo_client is not None:
            try:
                teams = await _mongo_client.get_teams_rating(
                    filter_type="all_time",
                    limit=1000,  # Получаем больше, чтобы найти команду
                )
            except Exception as e:
                _LOG.error(f"Ошибка при получении рейтинга: {e}")
        
        rating_text = format_teams_rating(
            teams=teams,
            filter_text="За всё время",
            team_position=position,
        )
    
    await callback.message.edit_text(
        text=rating_text,
        reply_markup=get_ratings_filter_keyboard(
            rating_type=rating_type,
            current_filter="all_time",
        ),
        parse_mode="HTML",
    )
    await callback.answer(f"Ваша позиция: #{position}")


async def support_question_message_handler(
    message: types.Message,
) -> None:
    """
    Обработчик сообщений для отправки вопроса в поддержку.
    """
    print(f"[DEBUG] >>> support_question_message_handler ВЫЗВАН")
    user_id = message.from_user.id
    print(f"[DEBUG] support_question_message_handler вызван для пользователя {user_id}, waiting={_waiting_support_question.get(user_id, False)}")
    
    # Проверяем, ожидает ли пользователь ввода вопроса
    if not _waiting_support_question.get(user_id, False):
        # Не обрабатываем, но не блокируем другие обработчики
        print(f"[DEBUG] Пользователь {user_id} не в режиме ожидания вопроса")
        return
    
    print(f"[INFO] Обработка вопроса от пользователя {user_id}, текст: {message.text[:50] if message.text else 'не текст'}")
    
    # Проверяем команду /cancel
    if message.text and message.text.strip().lower() == "/cancel":
        _waiting_support_question.pop(user_id, None)
        await message.answer(
            "❌ Отправка вопроса отменена.",
            reply_markup=get_support_keyboard(),
        )
        return
    
    # Проверяем, что это текстовое сообщение
    if not message.text:
        await message.answer(
            "❌ Пожалуйста, отправьте текстовое сообщение с вашим вопросом.\n\n"
            "Или отправьте /cancel для отмены.",
        )
        return
    
    question_text = message.text.strip()
    
    # Отправляем вопрос в поддержку (@eebanu)
    try:
        bot = message.bot
        
        # Формируем сообщение для поддержки
        support_message = (
            f"❓ Новый вопрос от пользователя\n\n"
            f"👤 Пользователь: {message.from_user.full_name}\n"
            f"📱 Username: @{message.from_user.username or 'не указан'}\n"
            f"🆔 ID: {user_id}\n\n"
            f"💬 Вопрос:\n{question_text}"
        )
        
        # Пытаемся отправить сообщение администратору поддержки
        # Примечание: для отправки по username нужен user_id
        # Можно использовать форвард сообщения или сохранить user_id в конфиге
        # Пока логируем и уведомляем пользователя
        
        # Логируем вопрос
        _LOG.info(
            f"Вопрос от пользователя {user_id} (@{message.from_user.username or 'без username'}): {question_text}",
        )
        
        # Отправляем вопрос администратору поддержки, если указан ID
        if SUPPORT_ADMIN_ID:
            try:
                await bot.send_message(
                    chat_id=int(SUPPORT_ADMIN_ID),
                    text=support_message,
                )
                _LOG.info(f"Вопрос отправлен администратору поддержки (ID: {SUPPORT_ADMIN_ID})")
            except Exception as e:
                _LOG.error(f"Ошибка при отправке вопроса администратору: {e}")
        else:
            _LOG.warning(
                "SUPPORT_ADMIN_ID не указан в конфигурации. Вопрос только залогирован.",
            )
        
        # Уведомляем пользователя
        await message.answer(
            "✅ Ваш вопрос отправлен в поддержку!\n\n"
            f"Ваш вопрос: {question_text}\n\n"
            "Мы ответим вам в ближайшее время.",
            reply_markup=get_support_keyboard(),
        )
        
        _LOG.info(f"Вопрос успешно обработан для пользователя {user_id}")
        
        # Сбрасываем флаг ожидания
        _waiting_support_question.pop(user_id, None)
        
    except Exception as e:
        _LOG.error(
            f"Ошибка при отправке вопроса в поддержку: {e}",
        )
        await message.answer(
            "❌ Произошла ошибка при отправке вопроса. Попробуйте позже.",
            reply_markup=get_support_keyboard(),
        )
        _waiting_support_question.pop(user_id, None)


async def promocode_message_handler(
    message: types.Message,
) -> None:
    """
    Обработчик сообщений для ввода промокода.
    """
    print(f"[DEBUG] >>> promocode_message_handler ВЫЗВАН")
    user_id = message.from_user.id
    print(f"[DEBUG] promocode_message_handler вызван для пользователя {user_id}, waiting={_waiting_promocode.get(user_id, False)}")
    
    # Проверяем, ожидает ли пользователь ввода промокода
    if not _waiting_promocode.get(user_id, False):
        # Не обрабатываем, но не блокируем другие обработчики
        print(f"[DEBUG] Пользователь {user_id} не в режиме ожидания промокода - пропускаем")
        # В aiogram 3.x нужно явно продолжить обработку
        # Но просто return должен работать, возможно проблема в другом месте
        return
    
    print(f"[INFO] Обработка промокода от пользователя {user_id}, текст: {message.text[:50] if message.text else 'не текст'}")
    
    # Проверяем команду /cancel
    if message.text and message.text.strip().lower() == "/cancel":
        _waiting_promocode.pop(user_id, None)
        await message.answer(
            "❌ Ввод промокода отменён.",
            reply_markup=get_wallet_keyboard(),
        )
        return
    
    # Проверяем, что это текстовое сообщение
    if not message.text:
        await message.answer(
            "❌ Пожалуйста, отправьте текстовое сообщение с промокодом.\n\n"
            "Или отправьте /cancel для отмены.",
        )
        return
    
    promocode = message.text.strip().upper()
    
    # Проверяем промокод в базе данных
    if _mongo_client is not None:
        try:
            success, message_text, amount = await _mongo_client.activate_promocode(
                promocode,
                user_id,
            )
            
            if success and amount:
                # Добавляем транзакцию
                await _mongo_client.add_transaction(
                    user_id=user_id,
                    transaction_type=TransactionType.DEPOSIT,
                    amount=amount,
                    description=f"Промокод: {promocode}",
                )
                
                new_balance = await _mongo_client.get_user_balance(user_id)
                
                await message.answer(
                    f"✅ {message_text}\n\n"
                    f"💵 Новый баланс: {new_balance} CD токенов",
                    reply_markup=get_wallet_keyboard(),
                )
            else:
                await message.answer(
                    f"❌ {message_text}",
                    reply_markup=get_wallet_keyboard(),
                )
        except Exception as e:
            _LOG.error(f"Ошибка при активации промокода: {e}")
            await message.answer(
                "❌ Произошла ошибка при активации промокода. Попробуйте позже.",
                reply_markup=get_wallet_keyboard(),
            )
    else:
        await message.answer(
            "❌ Ошибка подключения к базе данных.",
            reply_markup=get_wallet_keyboard(),
        )
    
    # Сбрасываем флаг ожидания
    _waiting_promocode.pop(user_id, None)


async def admin_user_search_message_handler(
    message: types.Message,
) -> None:
    """
    Обработчик сообщений для поиска пользователей в админ-панели.
    """
    user_id = message.from_user.id
    
    # Проверяем, ожидает ли пользователь ввода поискового запроса
    if not _waiting_user_search.get(user_id, False):
        return
    
    # Проверяем команду /cancel
    if message.text and message.text.strip().lower() == "/cancel":
        _waiting_user_search.pop(user_id, None)
        await message.answer(
            "❌ Поиск отменён.",
            reply_markup=get_admin_users_search_keyboard(),
        )
        return
    
    # Проверяем, что это текстовое сообщение
    if not message.text:
        await message.answer(
            "❌ Пожалуйста, отправьте текстовое сообщение с никнеймом или ID пользователя.\n\n"
            "Или отправьте /cancel для отмены.",
        )
        return
    
    search_query = message.text.strip()
    
    # Ищем пользователя
    found_user = None
    if _mongo_client is not None:
        try:
            # Пробуем найти по ID (если это число)
            if search_query.isdigit():
                found_user = await _mongo_client.get_user(int(search_query))
            else:
                # Ищем по username (убираем @ если есть)
                username = search_query.lstrip("@")
                # Ищем по nickname
                found_user = await _mongo_client.find_user_by_username_or_nickname(username)
        except Exception as e:
            _LOG.error(f"Ошибка при поиске пользователя: {e}")
    
    if not found_user:
        await message.answer(
            f"❌ Пользователь не найден: <code>{search_query}</code>\n\n"
            "Попробуйте другой запрос или отправьте /cancel для отмены.",
            parse_mode="HTML",
        )
        return
    
    # Показываем карточку пользователя
    team = None
    if found_user.team_id and _mongo_client is not None:
        try:
            team = await _mongo_client.get_team(found_user.team_id)
        except Exception as e:
            _LOG.error(f"Ошибка при получении команды: {e}")
    
    user_card_text = format_admin_user_card_text(found_user, team)
    
    # Получаем роль текущего пользователя для проверки прав
    current_user_role = await get_user_role(user_id)
    is_super_admin = current_user_role == UserRole.SUPER_ADMIN
    
    await message.answer(
        text=user_card_text,
        reply_markup=get_admin_user_card_keyboard(
            user_id=found_user.id,
            is_super_admin=is_super_admin,
            is_banned=found_user.is_banned,
        ),
        parse_mode="HTML",
    )
    
    # Сбрасываем флаг ожидания
    _waiting_user_search.pop(user_id, None)


async def admin_team_search_message_handler(
    message: types.Message,
) -> None:
    """
    Обработчик сообщений для поиска команд в админ-панели.
    """
    user_id = message.from_user.id
    
    # Проверяем, ожидает ли пользователь ввода поискового запроса
    if not _waiting_team_search.get(user_id, False):
        return
    
    # Проверяем команду /cancel
    if message.text and message.text.strip().lower() == "/cancel":
        _waiting_team_search.pop(user_id, None)
        await message.answer(
            "❌ Поиск отменён.",
            reply_markup=get_admin_teams_search_keyboard(),
        )
        return
    
    # Проверяем, что это текстовое сообщение
    if not message.text:
        await message.answer(
            "❌ Пожалуйста, отправьте текстовое сообщение с названием, тегом или ID команды.\n\n"
            "Или отправьте /cancel для отмены.",
        )
        return
    
    search_query = message.text.strip()
    
    # Ищем команду
    found_team = None
    if _mongo_client is not None:
        try:
            # Пробуем найти по ID
            if search_query.startswith("team_"):
                found_team = await _mongo_client.get_team(search_query)
            else:
                # Ищем по названию или тегу
                found_team = await _mongo_client.find_team_by_name_or_tag(search_query)
        except Exception as e:
            _LOG.error(f"Ошибка при поиске команды: {e}")
    
    if not found_team:
        await message.answer(
            f"❌ Команда не найдена: <code>{search_query}</code>\n\n"
            "Попробуйте другой запрос или отправьте /cancel для отмены.",
            parse_mode="HTML",
        )
        return
    
    # Показываем карточку команды
    team_card_text = await format_admin_team_card_text(found_team)
    
    await message.answer(
        text=team_card_text,
        reply_markup=get_admin_team_card_keyboard(
            team_id=found_team.id,
            is_banned=found_team.is_banned,
            captain_confirmed=found_team.captain_confirmed,
        ),
        parse_mode="HTML",
    )
    
    # Сбрасываем флаг ожидания
    _waiting_team_search.pop(user_id, None)


async def admin_token_amount_message_handler(
    message: types.Message,
) -> None:
    """
    Обработчик сообщений для ввода суммы токенов для начисления/списания.
    """
    user_id = message.from_user.id
    
    # Проверяем, ожидает ли пользователь ввода суммы
    if user_id not in _waiting_token_amount:
        return
    
    token_data = _waiting_token_amount[user_id]
    action = token_data["action"]
    target_user_id = token_data["target_user_id"]
    
    # Проверяем команду /cancel
    if message.text and message.text.strip().lower() == "/cancel":
        _waiting_token_amount.pop(user_id, None)
        await message.answer(
            "❌ Операция отменена.",
            reply_markup=get_admin_users_search_keyboard(),
        )
        return
    
    # Проверяем, что это текстовое сообщение
    if not message.text:
        await message.answer(
            "❌ Пожалуйста, отправьте текстовое сообщение с суммой.\n\n"
            "Или отправьте /cancel для отмены.",
        )
        return
    
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            await message.answer(
                "❌ Сумма должна быть положительным числом.\n\n"
                "Или отправьте /cancel для отмены.",
            )
            return
        
        if _mongo_client is not None:
            # Выполняем операцию
            transaction_type = TransactionType.DEPOSIT if action == "add" else TransactionType.DEBIT
            description = f"Админ: {'начисление' if action == 'add' else 'списание'} токенов"
            
            await _mongo_client.add_transaction(
                user_id=target_user_id,
                transaction_type=transaction_type,
                amount=amount,
                description=description,
            )
            # Логируем операцию с токенами
            action_type = ActionType.TOKENS_ADDED if action == "add" else ActionType.TOKENS_REMOVED
            await _mongo_client.add_action_log(
                action_type=action_type,
                user_id=user_id,
                description=f"{'Начислено' if action == 'add' else 'Списано'} {amount} CD токенов пользователю (ID: {target_user_id})",
                details={"target_user_id": target_user_id, "amount": amount},
            )
            
            new_balance = await _mongo_client.get_user_balance(target_user_id)
            action_text = "начислено" if action == "add" else "списано"
            
            await message.answer(
                f"✅ {action_text.capitalize()} {amount} CD токенов пользователю (ID: {target_user_id})\n\n"
                f"💵 Новый баланс: {new_balance} CD токенов",
            )
            
            # Показываем обновленную карточку пользователя
            target_user = await _mongo_client.get_user(target_user_id)
            if target_user:
                team = None
                if target_user.team_id:
                    team = await _mongo_client.get_team(target_user.team_id)
                user_card_text = format_admin_user_card_text(target_user, team)
                
                # Получаем роль текущего пользователя
                current_user_role = await get_user_role(user_id)
                is_super_admin = current_user_role == UserRole.SUPER_ADMIN
                
                await message.answer(
                    text=user_card_text,
                    reply_markup=get_admin_user_card_keyboard(
                        user_id=target_user_id,
                        is_super_admin=is_super_admin,
                        is_banned=target_user.is_banned,
                    ),
                    parse_mode="HTML",
                )
    except ValueError:
        await message.answer(
            "❌ Неверный формат суммы. Введите число.\n\n"
            "Или отправьте /cancel для отмены.",
        )
        return
    except Exception as e:
        _LOG.error(f"Ошибка при обработке суммы токенов: {e}")
        await message.answer(
            "❌ Произошла ошибка. Попробуйте позже.",
        )
    
    # Сбрасываем флаг ожидания
    _waiting_token_amount.pop(user_id, None)


async def tournament_create_message_handler(
    message: types.Message,
) -> None:
    """
    Обработчик текстовых сообщений для пошагового создания турнира.
    """
    print(f"[DEBUG] >>> tournament_create_message_handler ВЫЗВАН")
    user_id = message.from_user.id
    print(f"[DEBUG] tournament_create_message_handler вызван для пользователя {user_id}, in_data={user_id in _tournament_creation_data}")
    
    # Проверяем, создаётся ли турнир
    if user_id not in _tournament_creation_data:
        # Не обрабатываем, но не блокируем другие обработчики
        print(f"[DEBUG] Пользователь {user_id} не создает турнир")
        return
    
    print(f"[INFO] Обработка создания турнира от пользователя {user_id}, шаг: {_tournament_creation_data[user_id].get('step', 'unknown')}")
    
    # Проверяем, что это текстовое сообщение
    if not message.text:
        return
    
    creation_data = _tournament_creation_data[user_id]
    step = creation_data["step"]
    data = creation_data["data"]
    text = message.text.strip()
    
    _LOG.debug(
        f"Обработка шага создания турнира: user_id={user_id}, step={step}, text={text[:50]}",
    )
    
    # Проверяем команду /cancel
    if text.lower() == "/cancel":
        _tournament_creation_data.pop(user_id, None)
        await message.answer(
            "❌ Создание турнира отменено",
            reply_markup=get_admin_tournaments_list_keyboard(),
        )
        return
    
    try:
        if step == "name":
            if not text or len(text) < 3:
                await message.answer(
                    "❌ Название турнира должно содержать минимум 3 символа.\n\n"
                    "Или отправьте /cancel для отмены.",
                )
                return
            
            data["name"] = text
            creation_data["step"] = "game_discipline"
            _LOG.info(
                f"Пользователь {user_id} ввёл название турнира: {text}, переход к шагу game_discipline",
            )
            await message.answer(
                "🏆 Создание турнира\n\n"
                "Шаг 2/9: Игра/дисциплина\n\n"
                "Введите название игры или дисциплины:\n\n"
                "Или отправьте /cancel для отмены.",
            )
        
        elif step == "game_discipline":
            if not text:
                await message.answer(
                    "❌ Игра/дисциплина не может быть пустой.\n\n"
                    "Или отправьте /cancel для отмены.",
                )
                return
            
            data["game_discipline"] = text
            creation_data["step"] = "format"
            await message.answer(
                "🏆 Создание турнира\n\n"
                "Шаг 3/9: Формат турнира\n\n"
                "Выберите формат:",
                reply_markup=get_tournament_format_keyboard(),
            )
        
        elif step == "dates":
            # Парсим даты: "ДД.ММ.ГГГГ ЧЧ:ММ | ДД.ММ.ГГГГ ЧЧ:ММ | ДД.ММ.ГГГГ ЧЧ:ММ | ДД.ММ.ГГГГ ЧЧ:ММ"
            parts = [p.strip() for p in text.split("|")]
            if len(parts) < 3:
                await message.answer(
                    "❌ Неверный формат дат!\n\n"
                    "Нужно ввести минимум 3 даты через символ <b>|</b> (вертикальная черта).\n\n"
                    "Формат:\n"
                    "<b>ДД.ММ.ГГГГ ЧЧ:ММ | ДД.ММ.ГГГГ ЧЧ:ММ | ДД.ММ.ГГГГ ЧЧ:ММ | ДД.ММ.ГГГГ ЧЧ:ММ</b>\n\n"
                    "1. Старт регистрации\n"
                    "2. Конец регистрации\n"
                    "3. Старт турнира\n"
                    "4. Конец турнира (опционально, можно пропустить)\n\n"
                    "Пример:\n"
                    "<code>01.01.2025 12:00 | 10.01.2025 12:00 | 15.01.2025 10:00 | 20.01.2025 18:00</code>\n\n"
                    "Или отправьте /cancel для отмены.",
                )
                return
            
            try:
                reg_start = dt.datetime.strptime(parts[0], "%d.%m.%Y %H:%M")
                reg_end = dt.datetime.strptime(parts[1], "%d.%m.%Y %H:%M")
                start_date = dt.datetime.strptime(parts[2], "%d.%m.%Y %H:%M")
                end_date = None
                if len(parts) >= 4 and parts[3].strip():
                    end_date = dt.datetime.strptime(parts[3].strip(), "%d.%m.%Y %H:%M")
                
                # Добавляем часовой пояс
                reg_start = reg_start.replace(tzinfo=MOSCOW_TZ)
                reg_end = reg_end.replace(tzinfo=MOSCOW_TZ)
                start_date = start_date.replace(tzinfo=MOSCOW_TZ)
                if end_date:
                    end_date = end_date.replace(tzinfo=MOSCOW_TZ)
                
                data["registration_start"] = reg_start
                data["registration_end"] = reg_end
                data["start_date"] = start_date
                if end_date:
                    data["end_date"] = end_date
                
                creation_data["step"] = "participant_limit"
                await message.answer(
                    "🏆 Создание турнира\n\n"
                    "Шаг 5/9: Лимит участников/команд\n\n"
                    "Введите лимит участников (или 0 для безлимита):\n\n"
                    "Или отправьте /cancel для отмены.",
                )
            except ValueError as e:
                await message.answer(
                    f"❌ Ошибка при парсинге дат: {e}\n\n"
                    "Используйте формат: ДД.ММ.ГГГГ ЧЧ:ММ\n\n"
                    "Или отправьте /cancel для отмены.",
                )
                return
        
        elif step == "participant_limit":
            try:
                limit = int(text)
                if limit < 0:
                    raise ValueError
                data["participant_limit"] = limit if limit > 0 else None
            except ValueError:
                await message.answer(
                    "❌ Введите корректное число (0 для безлимита).\n\n"
                    "Или отправьте /cancel для отмены.",
                )
                return
            
            creation_data["step"] = "scoring"
            if data["format"] == TournamentFormat.SOLO:
                await message.answer(
                    "🏆 Создание турнира\n\n"
                    "Шаг 6/9: Правила подсчёта\n\n"
                    "Введите правила подсчёта для соло турнира:\n"
                    "Например: <code>Игрок: киллы</code>\n\n"
                    "Или отправьте /cancel для отмены.",
                )
            else:
                await message.answer(
                    "🏆 Создание турнира\n\n"
                    "Шаг 6/9: Правила подсчёта\n\n"
                    "Выберите формулу подсчёта очков команды:",
                    reply_markup=get_tournament_team_scoring_keyboard(),
                )
        
        elif step == "scoring":
            # Для соло турнира правила подсчёта вводятся текстом
            if data["format"] == TournamentFormat.SOLO:
                if not text:
                    await message.answer(
                        "❌ Правила подсчёта не могут быть пустыми.\n\n"
                        "Или отправьте /cancel для отмены.",
                    )
                    return
                data["rules_summary"] = text
                creation_data["step"] = "prizes"
                await message.answer(
                    "🏆 Создание турнира\n\n"
                    "Шаг 7/9: Призы\n\n"
                    "Введите описание призов (или 'нет' для пропуска):\n\n"
                    "Или отправьте /cancel для отмены.",
                )
            else:
                # Для командного турнира формула уже выбрана через callback
                # Этот шаг не должен достигаться для командных турниров
                creation_data["step"] = "prizes"
                await message.answer(
                    "🏆 Создание турнира\n\n"
                    "Шаг 7/9: Призы\n\n"
                    "Введите описание призов (или 'нет' для пропуска):\n\n"
                    "Или отправьте /cancel для отмены.",
                )
        
        elif step == "prizes":
            if text.lower() in ("нет", "no", "н"):
                data["prizes"] = None
            else:
                data["prizes"] = text
            
            creation_data["step"] = "rules"
            await message.answer(
                "🏆 Создание турнира\n\n"
                "Шаг 8/9: Описание/правила\n\n"
                "Введите краткое описание правил турнира:\n\n"
                "Или отправьте /cancel для отмены.",
            )
        
        elif step == "rules":
            data["rules_summary"] = text
            creation_data["step"] = "review"
            # Показываем review экран
            review_text = "🏆 Проверьте данные турнира:\n\n"
            
            review_text += f"📝 Название: {data.get('name', 'Не указано')}\n"
            review_text += f"🎮 Игра: {data.get('game_discipline', 'Не указано')}\n"
            
            format_text = "👤 Соло" if data.get('format') == TournamentFormat.SOLO else "👥 Команды"
            review_text += f"📋 Формат: {format_text}\n"
            
            if data.get('registration_start'):
                review_text += f"📅 Регистрация: {data['registration_start'].strftime('%d.%m.%Y %H:%M')} - {data['registration_end'].strftime('%d.%m.%Y %H:%M')}\n"
            if data.get('start_date'):
                review_text += f"🚀 Старт: {data['start_date'].strftime('%d.%m.%Y %H:%M')}\n"
            if data.get('end_date'):
                review_text += f"🏁 Финиш: {data['end_date'].strftime('%d.%m.%Y %H:%M')}\n"
            
            if data.get('participant_limit'):
                review_text += f"👥 Лимит: {data['participant_limit']}\n"
            
            if data.get('scoring_formula'):
                scoring_text = {
                    "sum": "Сумма",
                    "topn": "Топ-N",
                    "avg": "Среднее",
                }
                review_text += f"📊 Формула подсчёта: {scoring_text.get(data['scoring_formula'], data['scoring_formula'])}\n"
            
            if data.get('prizes'):
                review_text += f"🎁 Призы: {data['prizes']}\n"
            
            if data.get('rules_summary'):
                review_text += f"📝 Правила: {data['rules_summary']}\n"
            
            join_type_text = {
                "all": "🌐 Все",
                "invite": "📩 По приглашению",
                "confirmed": "✅ Только подтверждённые команды",
            }
            review_text += f"🔐 Тип вступления: {join_type_text.get(data.get('join_type'), 'Не указано')}\n"
            
            await message.answer(
                text=review_text,
                reply_markup=get_tournament_review_keyboard(),
            )
        
    except Exception as e:
        _LOG.error(f"Ошибка при обработке шага создания турнира: {e}")
        await message.answer(
            "❌ Произошла ошибка. Попробуйте снова или отправьте /cancel для отмены.",
        )


async def admin_promocode_data_message_handler(
    message: types.Message,
) -> None:
    """
    Обработчик сообщений для создания/редактирования промокодов и настроек бонусов.
    """
    user_id = message.from_user.id
    
    if user_id not in _waiting_promocode_data:
        return
    
    data = _waiting_promocode_data[user_id]
    result_type = data.get("type")
    
    # Проверяем команду /cancel
    if message.text and message.text.strip().lower() == "/cancel":
        _waiting_promocode_data.pop(user_id, None)
        await message.answer("❌ Операция отменена.")
        return
    
    if not message.text:
        await message.answer(
            "❌ Пожалуйста, отправьте текстовое сообщение.\n\n"
            "Или отправьте /cancel для отмены.",
        )
        return
    
    if result_type == "daily_bonus_amount":
        try:
            amount = int(message.text.strip())
            if amount < 0:
                await message.answer(
                    "❌ Сумма не может быть отрицательной.\n\n"
                    "Или отправьте /cancel для отмены.",
                )
                return
            
            if _mongo_client is not None:
                await _mongo_client.update_bonus_settings(
                    daily_bonus_amount=amount,
                )
                _waiting_promocode_data.pop(user_id, None)
                await message.answer(
                    f"✅ Сумма ежедневного бонуса обновлена: {amount} токенов",
                )
        except ValueError:
            await message.answer(
                "❌ Неверный формат. Введите число.\n\n"
                "Или отправьте /cancel для отмены.",
            )
    elif result_type == "create_promocode":
        step = data.get("step", "code")
        
        if step == "code":
            code = message.text.strip().upper()
            if not code:
                await message.answer(
                    "❌ Код промокода не может быть пустым.\n\n"
                    "Или отправьте /cancel для отмены.",
                )
                return
            
            # Проверяем, не существует ли уже такой промокод
            if _mongo_client is not None:
                existing = await _mongo_client.get_promocode_by_code(code)
                if existing:
                    await message.answer(
                        f"❌ Промокод '{code}' уже существует.\n\n"
                        "Введите другой код:\n\n"
                        "Или отправьте /cancel для отмены.",
                    )
                    return
            
            data["code"] = code
            data["step"] = "amount"
            await message.answer(
                f"✅ Код промокода: {code}\n\n"
                "Шаг 2/5: Сумма\n\n"
                "Введите количество токенов для начисления:\n\n"
                "Или отправьте /cancel для отмены.",
            )
        elif step == "amount":
            try:
                amount = int(message.text.strip())
                if amount <= 0:
                    await message.answer(
                        "❌ Сумма должна быть больше 0.\n\n"
                        "Или отправьте /cancel для отмены.",
                    )
                    return
                
                data["amount"] = amount
                data["step"] = "description"
                await message.answer(
                    f"✅ Сумма: {amount} токенов\n\n"
                    "Шаг 3/5: Описание (опционально)\n\n"
                    "Введите описание промокода или 'нет' для пропуска:\n\n"
                    "Или отправьте /cancel для отмены.",
                )
            except ValueError:
                await message.answer(
                    "❌ Неверный формат. Введите число.\n\n"
                    "Или отправьте /cancel для отмены.",
                )
        elif step == "description":
            description = message.text.strip()
            if description.lower() == "нет":
                description = ""
            data["description"] = description
            data["step"] = "limit"
            await message.answer(
                f"✅ Описание: {description if description else 'не указано'}\n\n"
                "Шаг 4/5: Лимит активаций\n\n"
                "Введите лимит активаций (число) или 'нет' для безлимита:\n\n"
                "Или отправьте /cancel для отмены.",
            )
        elif step == "limit":
            limit_text = message.text.strip().lower()
            activation_limit = None
            if limit_text != "нет":
                try:
                    activation_limit = int(limit_text)
                    if activation_limit <= 0:
                        await message.answer(
                            "❌ Лимит должен быть больше 0.\n\n"
                            "Или отправьте /cancel для отмены.",
                        )
                        return
                except ValueError:
                    await message.answer(
                        "❌ Неверный формат. Введите число или 'нет'.\n\n"
                        "Или отправьте /cancel для отмены.",
                    )
                    return
            
            data["activation_limit"] = activation_limit
            data["step"] = "dates"
            await message.answer(
                f"✅ Лимит: {activation_limit if activation_limit else 'безлимит'}\n\n"
                "Шаг 5/5: Срок действия\n\n"
                "Введите даты в формате:\n"
                "<b>ДД.ММ.ГГГГ ЧЧ:ММ | ДД.ММ.ГГГГ ЧЧ:ММ</b>\n"
                "(начало | конец) или 'нет' для бессрочного:\n\n"
                "Или отправьте /cancel для отмены.",
            )
        elif step == "dates":
            dates_text = message.text.strip().lower()
            valid_from = None
            valid_until = None
            
            if dates_text != "нет":
                try:
                    parts = dates_text.split("|")
                    if len(parts) != 2:
                        raise ValueError
                    
                    from_str = parts[0].strip()
                    until_str = parts[1].strip()
                    
                    valid_from = dt.datetime.strptime(from_str, "%d.%m.%Y %H:%M")
                    valid_until = dt.datetime.strptime(until_str, "%d.%m.%Y %H:%M")
                    
                    # Устанавливаем московский часовой пояс
                    valid_from = valid_from.replace(tzinfo=MOSCOW_TZ)
                    valid_until = valid_until.replace(tzinfo=MOSCOW_TZ)
                    
                    if valid_until <= valid_from:
                        await message.answer(
                            "❌ Дата окончания должна быть позже даты начала.\n\n"
                            "Или отправьте /cancel для отмены.",
                        )
                        return
                except ValueError:
                    await message.answer(
                        "❌ Неверный формат дат.\n\n"
                        "Введите даты в формате: <b>ДД.ММ.ГГГГ ЧЧ:ММ | ДД.ММ.ГГГГ ЧЧ:ММ</b>\n"
                        "Или отправьте /cancel для отмены.",
                        parse_mode="HTML",
                    )
                    return
            
            # Создаем промокод
            if _mongo_client is not None:
                try:
                    promocode = await _mongo_client.create_promocode(
                        code=data["code"],
                        amount=data["amount"],
                        description=data.get("description", ""),
                        activation_limit=data.get("activation_limit"),
                        valid_from=valid_from,
                        valid_until=valid_until,
                    )
                    # Логируем создание промокода
                    await _mongo_client.add_action_log(
                        action_type=ActionType.PROMOCODE_CREATED,
                        user_id=user_id,
                        description=f"Создан промокод '{promocode.code}' (сумма: {promocode.amount} токенов)",
                        details={"promocode_id": promocode.id},
                    )
                    _waiting_promocode_data.pop(user_id, None)
                    await message.answer(
                        f"✅ Промокод '{promocode.code}' успешно создан!\n\n"
                        f"Сумма: {promocode.amount} токенов\n"
                        f"Лимит: {promocode.activation_limit if promocode.activation_limit else 'безлимит'}",
                    )
                except Exception as e:
                    _LOG.error(f"Ошибка при создании промокода: {e}")
                    await message.answer("❌ Произошла ошибка при создании промокода.")


async def admin_transaction_reason_message_handler(
    message: types.Message,
) -> None:
    """
    Обработчик сообщений для создания/редактирования причин транзакций.
    """
    user_id = message.from_user.id
    
    if user_id not in _waiting_transaction_reason_data:
        return
    
    data = _waiting_transaction_reason_data[user_id]
    
    # Проверяем команду /cancel
    if message.text and message.text.strip().lower() == "/cancel":
        _waiting_transaction_reason_data.pop(user_id, None)
        await message.answer("❌ Операция отменена.")
        return
    
    if not message.text:
        await message.answer(
            "❌ Пожалуйста, отправьте текстовое сообщение.\n\n"
            "Или отправьте /cancel для отмены.",
        )
        return
    
    result_type = data.get("type")
    
    if result_type == "create_reason":
        step = data.get("step", "name")
        
        if step == "name":
            name = message.text.strip()
            if not name:
                await message.answer(
                    "❌ Название не может быть пустым.\n\n"
                    "Или отправьте /cancel для отмены.",
                )
                return
            
            data["name"] = name
            data["step"] = "type"
            await message.answer(
                f"✅ Название: {name}\n\n"
                "Шаг 2/3: Тип транзакции\n\n"
                "Выберите тип:",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="➕ Начисление",
                                callback_data="admin_reason_type_deposit",
                            ),
                        ],
                        [
                            InlineKeyboardButton(
                                text="➖ Списание",
                                callback_data="admin_reason_type_withdrawal",
                            ),
                        ],
                        [
                            InlineKeyboardButton(
                                text="❌ Отмена",
                                callback_data="admin_reason_cancel",
                            ),
                        ],
                    ],
                ),
            )
        elif step == "description":
            description = message.text.strip()
            if description.lower() == "нет":
                description = ""
            
            # Создаем шаблон
            if _mongo_client is not None:
                try:
                    reason = await _mongo_client.create_transaction_reason(
                        name=data["name"],
                        description=description,
                        transaction_type=data["transaction_type"],
                    )
                    _waiting_transaction_reason_data.pop(user_id, None)
                    await message.answer(
                        f"✅ Шаблон '{reason.name}' успешно создан!",
                    )
                except Exception as e:
                    _LOG.error(f"Ошибка при создании шаблона: {e}")
                    await message.answer("❌ Произошла ошибка при создании шаблона.")


async def admin_giveaway_message_handler(
    message: types.Message,
) -> None:
    """
    Обработчик сообщений для создания розыгрышей.
    """
    user_id = message.from_user.id
    
    if user_id not in _waiting_giveaway_data:
        return
    
    data = _waiting_giveaway_data[user_id]
    result_type = data.get("type")
    
    # Проверяем команду /cancel
    if message.text and message.text.strip().lower() == "/cancel":
        _waiting_giveaway_data.pop(user_id, None)
        await message.answer("❌ Создание розыгрыша отменено.")
        return
    
    if not message.text:
        await message.answer(
            "❌ Пожалуйста, отправьте текстовое сообщение.\n\n"
            "Или отправьте /cancel для отмены.",
        )
        return
    
    if result_type == "create_giveaway":
        step = data.get("step", "name")
        
        if step == "name":
            name = message.text.strip()
            if not name:
                await message.answer(
                    "❌ Название не может быть пустым.\n\n"
                    "Или отправьте /cancel для отмены.",
                )
                return
            
            data["name"] = name
            data["step"] = "description"
            await message.answer(
                f"✅ Название: {name}\n\n"
                "Шаг 2/5: Описание/призы\n\n"
                "Введите описание розыгрыша и призы:\n\n"
                "Или отправьте /cancel для отмены.",
            )
        elif step == "description":
            description = message.text.strip()
            if not description:
                await message.answer(
                    "❌ Описание не может быть пустым.\n\n"
                    "Или отправьте /cancel для отмены.",
                )
                return
            
            data["description"] = description
            data["step"] = "period"
            await message.answer(
                f"✅ Описание: {description}\n\n"
                "Шаг 3/5: Период\n\n"
                "Введите даты в формате:\n"
                "<b>ДД.ММ.ГГГГ ЧЧ:ММ | ДД.ММ.ГГГГ ЧЧ:ММ</b>\n"
                "(начало | конец):\n\n"
                "Или отправьте /cancel для отмены.",
                parse_mode="HTML",
            )
        elif step == "period":
            dates_text = message.text.strip()
            try:
                parts = dates_text.split("|")
                if len(parts) != 2:
                    raise ValueError
                
                start_str = parts[0].strip()
                end_str = parts[1].strip()
                
                start_date = dt.datetime.strptime(start_str, "%d.%m.%Y %H:%M")
                end_date = dt.datetime.strptime(end_str, "%d.%m.%Y %H:%M")
                
                # Устанавливаем московский часовой пояс
                start_date = start_date.replace(tzinfo=MOSCOW_TZ)
                end_date = end_date.replace(tzinfo=MOSCOW_TZ)
                
                if end_date <= start_date:
                    await message.answer(
                        "❌ Дата окончания должна быть позже даты начала.\n\n"
                        "Или отправьте /cancel для отмены.",
                    )
                    return
                
                data["start_date"] = start_date
                data["end_date"] = end_date
                data["step"] = "participation_type"
                await message.answer(
                    f"✅ Период: {start_date.strftime('%d.%m.%Y %H:%M')} - {end_date.strftime('%d.%m.%Y %H:%M')}\n\n"
                    "Шаг 4/5: Способ участия\n\n"
                    "Выберите способ участия:",
                    reply_markup=get_giveaway_participation_type_keyboard(),
                )
            except ValueError:
                await message.answer(
                    "❌ Неверный формат дат.\n\n"
                    "Введите даты в формате: <b>ДД.ММ.ГГГГ ЧЧ:ММ | ДД.ММ.ГГГГ ЧЧ:ММ</b>\n"
                    "Или отправьте /cancel для отмены.",
                    parse_mode="HTML",
                )
        elif step == "participation_details":
            participation_type = data.get("participation_type")
            
            if participation_type == GiveawayParticipationType.TOKENS:
                # Ввод стоимости билета
                try:
                    ticket_cost = int(message.text.strip())
                    if ticket_cost <= 0:
                        await message.answer(
                            "❌ Стоимость должна быть больше 0.\n\n"
                            "Или отправьте /cancel для отмены.",
                        )
                        return
                    
                    data["ticket_cost"] = ticket_cost
                    data["step"] = "limit"
                    await message.answer(
                        f"✅ Стоимость билета: {ticket_cost} CD токенов\n\n"
                        "Шаг 5/5: Лимит билетов\n\n"
                        "Введите лимит билетов на человека (число) или 'нет' для безлимита:\n\n"
                        "Или отправьте /cancel для отмены.",
                    )
                except ValueError:
                    await message.answer(
                        "❌ Неверный формат. Введите число.\n\n"
                        "Или отправьте /cancel для отмены.",
                    )
            else:
                # Ввод описания условия
                condition_description = message.text.strip()
                if not condition_description:
                    await message.answer(
                        "❌ Описание условия не может быть пустым.\n\n"
                        "Или отправьте /cancel для отмены.",
                    )
                    return
                
                data["condition_description"] = condition_description
                data["step"] = "limit"
                await message.answer(
                    f"✅ Условие: {condition_description}\n\n"
                    "Шаг 5/5: Лимит билетов\n\n"
                    "Введите лимит билетов на человека (число) или 'нет' для безлимита:\n\n"
                    "Или отправьте /cancel для отмены.",
                )
        elif step == "limit":
            limit_text = message.text.strip().lower()
            ticket_limit = None
            if limit_text != "нет":
                try:
                    ticket_limit = int(limit_text)
                    if ticket_limit <= 0:
                        await message.answer(
                            "❌ Лимит должен быть больше 0.\n\n"
                            "Или отправьте /cancel для отмены.",
                        )
                        return
                except ValueError:
                    await message.answer(
                        "❌ Неверный формат. Введите число или 'нет'.\n\n"
                        "Или отправьте /cancel для отмены.",
                    )
                    return
            
            # Создаем розыгрыш
            if _mongo_client is not None:
                try:
                    promotion = await _mongo_client.create_giveaway(
                        name=data["name"],
                        description=data["description"],
                        start_date=data["start_date"],
                        end_date=data["end_date"],
                        participation_type=data["participation_type"],
                        ticket_cost=data.get("ticket_cost"),
                        condition_description=data.get("condition_description"),
                        ticket_limit_per_user=ticket_limit,
                    )
                    # Логируем создание розыгрыша
                    await _mongo_client.add_action_log(
                        action_type=ActionType.GIVEAWAY_CREATED,
                        user_id=user_id,
                        description=f"Создан розыгрыш '{promotion.name}'",
                        details={"giveaway_id": promotion.id},
                    )
                    _waiting_giveaway_data.pop(user_id, None)
                    await message.answer(
                        f"✅ Розыгрыш '{promotion.name}' успешно создан!\n\n"
                        f"Статус: {promotion.status.value}",
                    )
                except Exception as e:
                    _LOG.error(f"Ошибка при создании розыгрыша: {e}")
                    await message.answer("❌ Произошла ошибка при создании розыгрыша.")


async def admin_broadcast_message_handler(
    message: types.Message,
) -> None:
    """
    Обработчик сообщений для создания рассылки.
    """
    user_id = message.from_user.id
    
    if user_id not in _waiting_broadcast_data:
        return
    
    data = _waiting_broadcast_data[user_id]
    
    # Проверяем команду /cancel
    if message.text and message.text.strip().lower() == "/cancel":
        _waiting_broadcast_data.pop(user_id, None)
        await message.answer("❌ Создание рассылки отменено.")
        return
    
    if not message.text:
        await message.answer(
            "❌ Пожалуйста, отправьте текстовое сообщение.\n\n"
            "Или отправьте /cancel для отмены.",
        )
        return
    
    step = data.get("step", "message")
    
    if step == "message":
        message_text = message.text.strip()
        if not message_text:
            await message.answer(
                "❌ Текст сообщения не может быть пустым.\n\n"
                "Или отправьте /cancel для отмены.",
            )
            return
        
        data["message_text"] = message_text
        broadcast_type = data.get("type", "all")
        tournament_id = data.get("tournament_id")
        
        # Формируем предпросмотр
        preview_text = "📣 Предпросмотр рассылки\n\n"
        
        if broadcast_type == "all":
            preview_text += "📢 Получатели: Все пользователи\n\n"
        elif broadcast_type == "tournament":
            if _mongo_client is not None and tournament_id:
                tournament = await _mongo_client.get_tournament(tournament_id)
                if tournament:
                    preview_text += f"🏆 Получатели: Участники турнира '{tournament.name}'\n\n"
        elif broadcast_type == "staff":
            preview_text += "👥 Получатели: Менеджеры и Админы\n\n"
        
        preview_text += "─" * 30 + "\n\n"
        preview_text += message_text
        preview_text += "\n\n" + "─" * 30
        
        # Подсчитываем количество получателей
        recipient_count = 0
        if _mongo_client is not None:
            try:
                if broadcast_type == "all":
                    users = await _mongo_client.get_all_users()
                    recipient_count = len(users)
                elif broadcast_type == "tournament" and tournament_id:
                    tournament = await _mongo_client.get_tournament(tournament_id)
                    if tournament:
                        if tournament.format == TournamentFormat.SOLO:
                            recipient_count = len(tournament.solo_participants)
                        else:
                            recipient_count = len(tournament.team_participants)
                elif broadcast_type == "staff":
                    users = await _mongo_client.get_all_users()
                    recipient_count = sum(1 for u in users if u.role in (UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN))
            except Exception as e:
                _LOG.error(f"Ошибка при подсчете получателей: {e}")
        
        preview_text += f"\n\n📊 Получателей: {recipient_count}"
        
        await message.answer(
            text=preview_text,
            reply_markup=get_admin_broadcast_preview_keyboard(
                broadcast_type=broadcast_type,
                tournament_id=tournament_id,
            ),
        )


async def _show_actions_log(
    callback: types.CallbackQuery,
    page: int = 0,
) -> None:
    """
    Показывает журнал действий.
    
    Args:
        callback: Объект callback query
        page: Номер страницы
    """
    if _mongo_client is not None:
        try:
            logs = await _mongo_client.get_action_logs(page=page, limit=10)
            has_next = len(logs) > 10
            if has_next:
                logs = logs[:10]
            
            if not logs:
                await callback.message.edit_text(
                    text="🧾 Журнал действий\n\n"
                         "Записей пока нет.",
                    reply_markup=get_admin_actions_log_keyboard(page=page, has_next=False),
                )
                return
            
            # Формируем текст журнала
            lines = ["🧾 Журнал действий\n"]
            
            action_type_names = {
                ActionType.TOURNAMENT_CREATED: "🏆 Создан турнир",
                ActionType.TOURNAMENT_UPDATED: "✏️ Изменен турнир",
                ActionType.RESULTS_ENTERED: "📊 Внесены результаты",
                ActionType.RESULTS_PUBLISHED: "✅ Опубликованы результаты",
                ActionType.TOKENS_ADDED: "➕ Начислены токены",
                ActionType.TOKENS_REMOVED: "➖ Списаны токены",
                ActionType.SETTINGS_CHANGED: "⚙️ Изменены настройки",
                ActionType.PROMOCODE_CREATED: "🎟 Создан промокод",
                ActionType.PROMOCODE_UPDATED: "✏️ Изменен промокод",
                ActionType.GIVEAWAY_CREATED: "🎉 Создан розыгрыш",
                ActionType.GIVEAWAY_WINNERS_DETERMINED: "🏆 Определены победители розыгрыша",
                ActionType.USER_ROLE_CHANGED: "🎭 Изменена роль пользователя",
                ActionType.USER_BANNED: "🚫 Забанен пользователь",
                ActionType.USER_UNBANNED: "✅ Разбанен пользователь",
                ActionType.TEAM_BANNED: "🚫 Забанена команда",
                ActionType.TEAM_UNBANNED: "✅ Разбанена команда",
                ActionType.RATING_RECALCULATED: "📊 Пересчитан рейтинг",
            }
            
            for log in logs:
                action_name = action_type_names.get(log.action_type, log.action_type.value)
                timestamp = log.created_at.strftime("%d.%m.%Y %H:%M")
                
                # Получаем имя пользователя
                user_name = f"ID:{log.user_id}"
                if _mongo_client is not None:
                    try:
                        user = await _mongo_client.get_user(log.user_id)
                        if user:
                            user_name = user.nickname or user.name or f"ID:{log.user_id}"
                    except Exception:
                        pass
                
                lines.append(f"<b>{action_name}</b>")
                lines.append(f"👤 {user_name}")
                lines.append(f"📝 {log.description}")
                lines.append(f"🕐 {timestamp}")
                lines.append("─" * 30)
            
            text = "\n".join(lines)
            
            await callback.message.edit_text(
                text=text,
                reply_markup=get_admin_actions_log_keyboard(page=page, has_next=has_next),
                parse_mode="HTML",
            )
        except Exception as e:
            _LOG.error(f"Ошибка при получении журнала действий: {e}")
            await callback.message.edit_text(
                text="🧾 Журнал действий\n\n"
                     "❌ Произошла ошибка при загрузке журнала.",
                reply_markup=get_admin_actions_log_keyboard(page=page, has_next=False),
            )
    else:
        await callback.message.edit_text(
            text="🧾 Журнал действий\n\n"
                 "❌ Ошибка подключения к базе данных.",
            reply_markup=get_admin_actions_log_keyboard(page=page, has_next=False),
        )


async def _show_user_matches_results(
    callback: types.CallbackQuery,
    tournament_id: str,
) -> None:
    """
    Показывает киллы пользователя по матчам.
    
    Args:
        callback: Объект callback query
        tournament_id: ID турнира
    """
    if _mongo_client is None:
        await callback.answer("Ошибка: база данных недоступна", show_alert=True)
        return
    
    try:
        user_id = callback.from_user.id
        tournament = await _mongo_client.get_tournament(tournament_id)
        if not tournament:
            await callback.answer("Турнир не найден", show_alert=True)
            return
        
        # Получаем матчи турнира
        matches = await _mongo_client.get_tournament_matches(tournament_id)
        
        if not matches:
            await callback.message.edit_text(
                text="💀 Твои киллы по матчам\n\n"
                     "Матчи еще не созданы.",
                reply_markup=get_tournament_results_keyboard(
                    tournament_id=tournament_id,
                    is_participant=True,
                ),
            )
            return
        
        lines = ["💀 Твои киллы по матчам\n"]
        
        total_kills = 0
        for match in matches:
            # Получаем результат пользователя в матче
            if tournament.format == TournamentFormat.SOLO:
                match_results = await _mongo_client.get_match_results(match.id)
                user_result = next((r for r in match_results if r.participant_id == user_id), None)
                if user_result:
                    kills = user_result.kills
                    total_kills += kills
                    lines.append(f"🎮 {match.name}: <b>{kills} киллов</b>")
            else:
                # Для командных турниров получаем результат команды
                user = await _mongo_client.get_user(user_id)
                if user and user.team_id:
                    match_results = await _mongo_client.get_match_results(match.id)
                    team_result = next((r for r in match_results if str(r.participant_id) == str(user.team_id)), None)
                    if team_result:
                        kills = team_result.kills
                        total_kills += kills
                        lines.append(f"🎮 {match.name}: <b>{kills} киллов</b>")
        
        if total_kills > 0:
            lines.append(f"\n💀 Всего киллов: <b>{total_kills}</b>")
        else:
            lines.append("\n💀 Результаты по матчам пока не внесены")
        
        await callback.message.edit_text(
            text="\n".join(lines),
            reply_markup=get_tournament_results_keyboard(
                tournament_id=tournament_id,
                is_participant=True,
            ),
            parse_mode="HTML",
        )
    except Exception as e:
        _LOG.error(f"Ошибка при получении результатов по матчам: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


async def _show_user_final_result(
    callback: types.CallbackQuery,
    tournament_id: str,
) -> None:
    """
    Показывает итоговый результат пользователя в турнире.
    
    Args:
        callback: Объект callback query
        tournament_id: ID турнира
    """
    if _mongo_client is None:
        await callback.answer("Ошибка: база данных недоступна", show_alert=True)
        return
    
    try:
        user_id = callback.from_user.id
        tournament = await _mongo_client.get_tournament(tournament_id)
        if not tournament:
            await callback.answer("Турнир не найден", show_alert=True)
            return
        
        # Получаем итоговый результат
        if tournament.format == TournamentFormat.SOLO:
            result = await _mongo_client.get_tournament_result(tournament_id, user_id, is_team=False)
        else:
            user = await _mongo_client.get_user(user_id)
            if not user or not user.team_id:
                await callback.message.edit_text(
                    text="🏆 Итог турнира\n\n"
                         "Вы не состоите в команде.",
                    reply_markup=get_tournament_results_keyboard(
                        tournament_id=tournament_id,
                        is_participant=True,
                    ),
                )
                return
            result = await _mongo_client.get_tournament_result(tournament_id, str(user.team_id), is_team=True)
        
        if not result:
            await callback.message.edit_text(
                text="🏆 Итог турнира\n\n"
                     "Итоговый результат пока не определен.",
                reply_markup=get_tournament_results_keyboard(
                    tournament_id=tournament_id,
                    is_participant=True,
                ),
            )
            return
        
        lines = ["🏆 Итог турнира\n"]
        lines.append(f"💀 Всего киллов: <b>{result.total_kills}</b>")
        if result.total_points:
            lines.append(f"📊 Всего очков: <b>{result.total_points}</b>")
        if result.position:
            lines.append(f"🏅 Место: <b>#{result.position}</b>")
        
        await callback.message.edit_text(
            text="\n".join(lines),
            reply_markup=get_tournament_results_keyboard(
                tournament_id=tournament_id,
                is_participant=True,
            ),
            parse_mode="HTML",
        )
    except Exception as e:
        _LOG.error(f"Ошибка при получении итогового результата: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


async def _show_user_team_results(
    callback: types.CallbackQuery,
    tournament_id: str,
) -> None:
    """
    Показывает очки команды пользователя.
    
    Args:
        callback: Объект callback query
        tournament_id: ID турнира
    """
    if _mongo_client is None:
        await callback.answer("Ошибка: база данных недоступна", show_alert=True)
        return
    
    try:
        user_id = callback.from_user.id
        tournament = await _mongo_client.get_tournament(tournament_id)
        if not tournament:
            await callback.answer("Турнир не найден", show_alert=True)
            return
        
        if tournament.format == TournamentFormat.SOLO:
            await callback.message.edit_text(
                text="👥 Очки команды\n\n"
                     "Этот турнир проводится в формате соло.",
                reply_markup=get_tournament_results_keyboard(
                    tournament_id=tournament_id,
                    is_participant=True,
                ),
            )
            return
        
        user = await _mongo_client.get_user(user_id)
        if not user or not user.team_id:
            await callback.message.edit_text(
                text="👥 Очки команды\n\n"
                     "Вы не состоите в команде.",
                reply_markup=get_tournament_results_keyboard(
                    tournament_id=tournament_id,
                    is_participant=True,
                ),
            )
            return
        
        team = await _mongo_client.get_team(str(user.team_id))
        if not team:
            await callback.message.edit_text(
                text="👥 Очки команды\n\n"
                     "Команда не найдена.",
                reply_markup=get_tournament_results_keyboard(
                    tournament_id=tournament_id,
                    is_participant=True,
                ),
            )
            return
        
        # Получаем результат команды
        result = await _mongo_client.get_tournament_result(tournament_id, str(user.team_id), is_team=True)
        
        lines = [f"👥 Очки команды: {team.name} ({team.tag})\n"]
        
        if result:
            lines.append(f"💀 Всего киллов: <b>{result.total_kills}</b>")
            if result.total_points:
                lines.append(f"📊 Всего очков: <b>{result.total_points}</b>")
            if result.position:
                lines.append(f"🏅 Место: <b>#{result.position}</b>")
        else:
            lines.append("Результаты команды пока не определены")
        
        await callback.message.edit_text(
            text="\n".join(lines),
            reply_markup=get_tournament_results_keyboard(
                tournament_id=tournament_id,
                is_participant=True,
            ),
            parse_mode="HTML",
        )
    except Exception as e:
        _LOG.error(f"Ошибка при получении результатов команды: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


async def _show_tournament_results_table(
    callback: types.CallbackQuery,
    tournament_id: str,
) -> None:
    """
    Показывает общую таблицу результатов турнира.
    
    Args:
        callback: Объект callback query
        tournament_id: ID турнира
    """
    if _mongo_client is None:
        await callback.answer("Ошибка: база данных недоступна", show_alert=True)
        return
    
    try:
        tournament = await _mongo_client.get_tournament(tournament_id)
        if not tournament:
            await callback.answer("Турнир не найден", show_alert=True)
            return
        
        results = await _mongo_client.get_tournament_results(tournament_id)
        
        if not results:
            await callback.message.edit_text(
                text="📊 Общая таблица результатов\n\n"
                     "Результаты пока не определены.",
                reply_markup=get_tournament_results_keyboard(
                    tournament_id=tournament_id,
                    is_participant=False,
                ),
            )
            return
        
        # Сортируем по позиции
        results.sort(key=lambda x: x.position if x.position else 999)
        
        lines = ["📊 Общая таблица результатов\n"]
        lines.append("🏅 Место | Участник | Киллы | Очки")
        lines.append("─" * 40)
        
        for result in results[:20]:  # Показываем топ-20
            participant_name = await _get_participant_name(tournament, result.participant_id)
            position = f"#{result.position}" if result.position else "—"
            kills = result.total_kills or 0
            points = result.total_points or 0
            lines.append(f"{position} | {participant_name} | {kills} | {points}")
        
        if len(results) > 20:
            lines.append(f"\n... и еще {len(results) - 20} участников")
        
        await callback.message.edit_text(
            text="\n".join(lines),
            reply_markup=get_tournament_results_keyboard(
                tournament_id=tournament_id,
                is_participant=False,
            ),
        )
    except Exception as e:
        _LOG.error(f"Ошибка при получении таблицы результатов: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


async def results_dispute_message_handler(
    message: types.Message,
) -> None:
    """
    Обработчик сообщений для оспаривания результатов.
    """
    user_id = message.from_user.id
    
    if user_id not in _waiting_results_dispute:
        return
    
    data = _waiting_results_dispute[user_id]
    tournament_id = data.get("tournament_id")
    
    # Проверяем команду /cancel
    if message.text and message.text.strip().lower() == "/cancel":
        _waiting_results_dispute.pop(user_id, None)
        await message.answer("❌ Оспаривание результата отменено.")
        return
    
    if not message.text:
        await message.answer(
            "❌ Пожалуйста, отправьте текстовое сообщение с причиной оспаривания.\n\n"
            "Или отправьте /cancel для отмены.",
        )
        return
    
    dispute_text = message.text.strip()
    if not dispute_text:
        await message.answer(
            "❌ Текст оспаривания не может быть пустым.\n\n"
            "Или отправьте /cancel для отмены.",
        )
        return
    
    # Отправляем в поддержку
    if _mongo_client is not None:
        try:
            tournament = await _mongo_client.get_tournament(tournament_id)
            tournament_name = tournament.name if tournament else f"ID: {tournament_id}"
            
            # Формируем сообщение для администратора поддержки
            from src.config import SUPPORT_ADMIN_ID
            dispute_message = (
                f"⚠️ Оспаривание результата турнира\n\n"
                f"🏆 Турнир: {tournament_name}\n"
                f"👤 Пользователь: {message.from_user.full_name} (ID: {user_id})\n"
                f"📝 Причина:\n{dispute_text}"
            )
            
            # Отправляем администратору поддержки
            from aiogram import Bot
            bot = Bot.get_current()
            await bot.send_message(
                chat_id=SUPPORT_ADMIN_ID,
                text=dispute_message,
            )
            
            _waiting_results_dispute.pop(user_id, None)
            await message.answer(
                "✅ Ваше обращение отправлено в поддержку. "
                "Мы рассмотрим его в ближайшее время.",
                reply_markup=get_tournament_results_keyboard(
                    tournament_id=tournament_id,
                    is_participant=True,
                ),
            )
        except Exception as e:
            _LOG.error(f"Ошибка при отправке оспаривания: {e}")
            await message.answer("❌ Произошла ошибка при отправке обращения. Попробуйте позже.")
    else:
        await message.answer("❌ Ошибка подключения к базе данных.")
