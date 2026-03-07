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
    created_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(tz=MOSCOW_TZ),
        description="Дата создания турнира",
    )
    updated_at: Optional[dt.datetime] = Field(
        None,
        description="Дата последнего обновления",
    )