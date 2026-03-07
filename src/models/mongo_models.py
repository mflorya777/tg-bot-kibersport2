from typing import Optional
from enum import Enum
from pydantic import (
    BaseModel,
    Field,
)
import datetime as dt

from src.models.user_roles import UserRole


MOSCOW_TZ = dt.timezone(dt.timedelta(hours=3))


class User(BaseModel):
    id: int = Field(
        ...,
        description="Telegram user_id",
    )
    #
    username: Optional[str] = Field(
        None,
        description="Юзернейм через @",
    )
    name: Optional[str] = Field(
        None,
        description="Имя",
    )
    surname: Optional[str] = Field(
        None,
        description="Фамилия",
    )
    father_name: Optional[str] = Field(
        None,
        description="Отчество",
    )
    #
    phone: Optional[str] = Field(
        None,
        description="Номер телефона",
    )
    #
    nickname: Optional[str] = Field(
        None,
        description="Никнейм игрока",
    )
    game_discipline: Optional[str] = Field(
        None,
        description="Игра/дисциплина",
    )
    region_country: Optional[str] = Field(
        None,
        description="Регион/страна",
    )
    #
    tournaments_played: int = Field(
        default=0,
        description="Количество сыгранных турниров",
    )
    total_kills: int = Field(
        default=0,
        description="Всего киллов",
    )
    rating_position: Optional[int] = Field(
        None,
        description="Место в рейтинге",
    )
    #
    role: UserRole = Field(
        default=UserRole.USER,
        description="Роль пользователя в системе",
    )
    created_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(tz=MOSCOW_TZ),
        description="Дата регистрации",
    )
    updated_at: Optional[dt.datetime] = Field(
        None,
        description="Дата последнего обновления",
    )
    #
    team_id: Optional[str] = Field(
        None,
        description="ID команды, в которой состоит пользователь",
    )
    #
    balance: int = Field(
        default=0,
        description="Баланс CD токенов",
    )
    #
    is_banned: bool = Field(
        default=False,
        description="Забанен ли пользователь",
    )
    #
    # Бонусы
    last_daily_bonus_date: Optional[dt.date] = Field(
        None,
        description="Дата последнего получения ежедневного бонуса",
    )
    referral_code: Optional[str] = Field(
        None,
        description="Реферальный код пользователя",
    )
    referred_by: Optional[int] = Field(
        None,
        description="Telegram user_id пользователя, который пригласил",
    )
    referrals_count: int = Field(
        default=0,
        description="Количество приглашенных друзей",
    )
    # Задания
    quests_completed: dict[str, bool] = Field(
        default_factory=dict,
        description="Словарь выполненных заданий: {quest_id: completed}",
    )


class Team(BaseModel):
    id: str = Field(
        ...,
        description="Уникальный ID команды",
    )
    name: str = Field(
        ...,
        description="Название команды",
    )
    tag: str = Field(
        ...,
        description="Тег команды (короткое название)",
    )
    captain_id: int = Field(
        ...,
        description="Telegram user_id капитана команды",
    )
    members: list[int] = Field(
        default_factory=list,
        description="Список Telegram user_id участников команды",
    )
    #
    tournaments_played: int = Field(
        default=0,
        description="Количество сыгранных турниров",
    )
    total_points: int = Field(
        default=0,
        description="Всего очков команды",
    )
    rating_position: Optional[int] = Field(
        None,
        description="Место в рейтинге",
    )
    #
    invite_code: str = Field(
        ...,
        description="Код-приглашение для вступления в команду",
    )
    is_banned: bool = Field(
        default=False,
        description="Забанена ли команда",
    )
    captain_confirmed: bool = Field(
        default=False,
        description="Подтвержден ли капитан команды администратором",
    )
    created_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(tz=MOSCOW_TZ),
        description="Дата создания команды",
    )
    updated_at: Optional[dt.datetime] = Field(
        None,
        description="Дата последнего обновления",
    )


class TournamentStatus(str, Enum):
    """
    Статусы турнира.
    """
    REGISTRATION_OPEN = "registration_open"  # Открыта регистрация
    IN_PROGRESS = "in_progress"  # Идёт
    COMPLETED = "completed"  # Завершён


class TournamentFormat(str, Enum):
    """
    Форматы турнира.
    """
    SOLO = "solo"  # Соло
    TEAM = "team"  # Команды


class Tournament(BaseModel):
    id: str = Field(
        ...,
        description="Уникальный ID турнира",
    )
    name: str = Field(
        ...,
        description="Название турнира",
    )
    game_discipline: str = Field(
        ...,
        description="Игра/дисциплина",
    )
    #
    registration_start: dt.datetime = Field(
        ...,
        description="Дата начала регистрации",
    )
    registration_end: dt.datetime = Field(
        ...,
        description="Дата окончания регистрации",
    )
    start_date: dt.datetime = Field(
        ...,
        description="Дата начала турнира",
    )
    end_date: Optional[dt.datetime] = Field(
        None,
        description="Дата окончания турнира",
    )
    #
    format: TournamentFormat = Field(
        ...,
        description="Формат турнира (соло/команды)",
    )
    status: TournamentStatus = Field(
        default=TournamentStatus.REGISTRATION_OPEN,
        description="Статус турнира",
    )
    #
    entry_fee: Optional[int] = Field(
        None,
        description="Взнос (в CD токенах), если есть",
    )
    prizes: Optional[str] = Field(
        None,
        description="Описание призов, если есть",
    )
    participant_limit: Optional[int] = Field(
        None,
        description="Лимит участников/команд",
    )
    #
    rules_summary: Optional[str] = Field(
        None,
        description="Короткие правила подсчёта",
    )
    full_rules: Optional[str] = Field(
        None,
        description="Полные правила турнира",
    )
    #
    solo_participants: list[int] = Field(
        default_factory=list,
        description="Список Telegram user_id участников (для соло)",
    )
    team_participants: list[str] = Field(
        default_factory=list,
        description="Список team_id команд-участников (для командного)",
    )
    #
    results_published: bool = Field(
        default=False,
        description="Опубликованы ли результаты турнира",
    )
    #
    created_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(tz=MOSCOW_TZ),
        description="Дата создания турнира",
    )
    updated_at: Optional[dt.datetime] = Field(
        None,
        description="Дата последнего обновления",
    )


class TransactionType(str, Enum):
    """
    Типы транзакций.
    """
    DEPOSIT = "deposit"  # Начисление
    WITHDRAWAL = "withdrawal"  # Списание


class Transaction(BaseModel):
    id: str = Field(
        ...,
        description="Уникальный ID транзакции",
    )
    user_id: int = Field(
        ...,
        description="Telegram user_id пользователя",
    )
    transaction_type: TransactionType = Field(
        ...,
        description="Тип транзакции (начисление/списание)",
    )
    amount: int = Field(
        ...,
        description="Сумма транзакции (в CD токенах)",
    )
    description: str = Field(
        ...,
        description="Описание операции (за что)",
    )
    created_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(tz=MOSCOW_TZ),
        description="Дата и время транзакции",
    )


class RatingMetric(str, Enum):
    """
    Метрики для рейтинга.
    """
    KILLS = "kills"  # Киллы (для игроков)
    POINTS = "points"  # Очки (для команд)


class RatingRules(BaseModel):
    """
    Правила расчета рейтинга.
    """
    id: str = Field(
        default="rating_rules",
        description="ID правил (всегда один экземпляр)",
    )
    player_metric: RatingMetric = Field(
        default=RatingMetric.KILLS,
        description="Основной показатель для рейтинга игроков",
    )
    team_metric: RatingMetric = Field(
        default=RatingMetric.POINTS,
        description="Основной показатель для рейтинга команд",
    )
    season_start_date: Optional[dt.date] = Field(
        None,
        description="Дата начала текущего сезона",
    )
    season_end_date: Optional[dt.date] = Field(
        None,
        description="Дата окончания текущего сезона",
    )
    updated_at: Optional[dt.datetime] = Field(
        None,
        description="Дата последнего обновления",
    )

class Match(BaseModel):
    """
    Матч/раунд в турнире.
    """
    id: str = Field(
        ...,
        description="Уникальный ID матча",
    )
    tournament_id: str = Field(
        ...,
        description="ID турнира",
    )
    name: str = Field(
        ...,
        description="Название матча/раунда",
    )
    round_number: Optional[int] = Field(
        None,
        description="Номер раунда (если есть)",
    )
    match_date: Optional[dt.datetime] = Field(
        None,
        description="Дата проведения матча",
    )
    is_completed: bool = Field(
        default=False,
        description="Завершен ли матч",
    )
    created_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(tz=MOSCOW_TZ),
        description="Дата создания матча",
    )
    updated_at: Optional[dt.datetime] = Field(
        None,
        description="Дата последнего обновления",
    )


class MatchResult(BaseModel):
    """
    Результат матча для игрока или команды.
    """
    id: str = Field(
        ...,
        description="Уникальный ID результата",
    )
    match_id: str = Field(
        ...,
        description="ID матча",
    )
    tournament_id: str = Field(
        ...,
        description="ID турнира",
    )
    player_id: Optional[int] = Field(
        None,
        description="Telegram user_id игрока (для соло турниров)",
    )
    team_id: Optional[str] = Field(
        None,
        description="ID команды (для командных турниров)",
    )
    kills: int = Field(
        default=0,
        description="Киллы игрока/команды в матче",
    )
    created_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(tz=MOSCOW_TZ),
        description="Дата создания результата",
    )
    updated_at: Optional[dt.datetime] = Field(
        None,
        description="Дата последнего обновления",
    )


class TournamentResult(BaseModel):
    """
    Итоговый результат турнира для игрока или команды.
    """
    id: str = Field(
        ...,
        description="Уникальный ID результата",
    )
    tournament_id: str = Field(
        ...,
        description="ID турнира",
    )
    player_id: Optional[int] = Field(
        None,
        description="Telegram user_id игрока (для соло турниров)",
    )
    team_id: Optional[str] = Field(
        None,
        description="ID команды (для командных турниров)",
    )
    total_kills: int = Field(
        default=0,
        description="Общее количество киллов за турнир",
    )
    total_points: int = Field(
        default=0,
        description="Общее количество очков за турнир",
    )
    position: Optional[int] = Field(
        None,
        description="Место в турнире",
    )
    is_published: bool = Field(
        default=False,
        description="Опубликованы ли результаты",
    )
    created_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(tz=MOSCOW_TZ),
        description="Дата создания результата",
    )
    updated_at: Optional[dt.datetime] = Field(
        None,
        description="Дата последнего обновления",
    )


class Promocode(BaseModel):
    """
    Промокод для начисления бонусов.
    """
    id: str = Field(
        ...,
        description="Уникальный ID промокода",
    )
    code: str = Field(
        ...,
        description="Код промокода (например, WELCOME)",
    )
    amount: int = Field(
        ...,
        description="Количество токенов для начисления",
    )
    description: str = Field(
        default="",
        description="Описание промокода",
    )
    is_active: bool = Field(
        default=True,
        description="Активен ли промокод",
    )
    valid_from: Optional[dt.datetime] = Field(
        None,
        description="Дата начала действия",
    )
    valid_until: Optional[dt.datetime] = Field(
        None,
        description="Дата окончания действия",
    )
    activation_limit: Optional[int] = Field(
        None,
        description="Лимит активаций (None = безлимит)",
    )
    activation_count: int = Field(
        default=0,
        description="Количество активаций",
    )
    created_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(tz=MOSCOW_TZ),
        description="Дата создания промокода",
    )
    updated_at: Optional[dt.datetime] = Field(
        None,
        description="Дата последнего обновления",
    )


class BonusSettings(BaseModel):
    """
    Настройки бонусов.
    """
    id: str = Field(
        default="bonus_settings",
        description="ID настроек (всегда один экземпляр)",
    )
    daily_bonus_enabled: bool = Field(
        default=True,
        description="Включен ли ежедневный бонус",
    )
    daily_bonus_amount: int = Field(
        default=10,
        description="Количество токенов ежедневного бонуса",
    )
    updated_at: Optional[dt.datetime] = Field(
        None,
        description="Дата последнего обновления",
    )


class TransactionReason(BaseModel):
    """
    Шаблон причины транзакции.
    """
    id: str = Field(
        ...,
        description="Уникальный ID шаблона",
    )
    name: str = Field(
        ...,
        description="Название причины",
    )
    description: str = Field(
        default="",
        description="Описание причины",
    )
    transaction_type: TransactionType = Field(
        ...,
        description="Тип транзакции (начисление/списание)",
    )
    is_active: bool = Field(
        default=True,
        description="Активен ли шаблон",
    )
    created_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(tz=MOSCOW_TZ),
        description="Дата создания шаблона",
    )


class GiveawayParticipationType(str, Enum):
    """
    Тип участия в розыгрыше.
    """
    TOKENS = "tokens"  # За CD токены
    CONDITION = "condition"  # За выполнение условия


class GiveawayStatus(str, Enum):
    """
    Статус розыгрыша.
    """
    DRAFT = "draft"  # Черновик
    ACTIVE = "active"  # Активен
    COMPLETED = "completed"  # Завершен


class Giveaway(BaseModel):
    """
    Розыгрыш/акция.
    """
    id: str = Field(
        ...,
        description="Уникальный ID розыгрыша",
    )
    name: str = Field(
        ...,
        description="Название розыгрыша",
    )
    description: str = Field(
        ...,
        description="Описание/призы",
    )
    start_date: dt.datetime = Field(
        ...,
        description="Дата начала розыгрыша",
    )
    end_date: dt.datetime = Field(
        ...,
        description="Дата окончания розыгрыша",
    )
    participation_type: GiveawayParticipationType = Field(
        ...,
        description="Способ участия",
    )
    ticket_cost: Optional[int] = Field(
        None,
        description="Стоимость билета в CD токенах (если participation_type == TOKENS)",
    )
    condition_description: Optional[str] = Field(
        None,
        description="Описание условия (если participation_type == CONDITION)",
    )
    ticket_limit_per_user: Optional[int] = Field(
        None,
        description="Лимит билетов на пользователя (None = безлимит)",
    )
    status: GiveawayStatus = Field(
        default=GiveawayStatus.DRAFT,
        description="Статус розыгрыша",
    )
    participants: dict[int, int] = Field(
        default_factory=dict,
        description="Участники: {user_id: количество_билетов}",
    )
    winners: list[int] = Field(
        default_factory=list,
        description="Список ID победителей",
    )
    created_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(tz=MOSCOW_TZ),
        description="Дата создания розыгрыша",
    )
    updated_at: Optional[dt.datetime] = Field(
        None,
        description="Дата последнего обновления",
    )
