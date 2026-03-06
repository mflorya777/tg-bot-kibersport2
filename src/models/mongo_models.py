from typing import Optional
from pydantic import (
    BaseModel,
    Field,
)
import datetime as dt


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
    created_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(tz=MOSCOW_TZ),
        description="Дата регистрации",
    )
    updated_at: Optional[dt.datetime] = Field(
        None,
        description="Дата последнего обновления",
    )
