import logging
from typing import Optional
import datetime as dt

from motor.motor_asyncio import AsyncIOMotorClient

from src.config import MongoConfig
from src.models.mongo_models import User


_LOG = logging.getLogger("woman-tg-bot")

MOSCOW_TZ = dt.timezone(dt.timedelta(hours=3))


class MongoClient:
    def __init__(self, config: MongoConfig):
        self.user = config.mongo_user
        self.password = config.mongo_password
        self.host = config.mongo_host
        self.port = config.mongo_port
        self.db_name = config.mongo_db_name
        self.enable_ssl = config.mongo_enable_ssl
        self.users_collection_name = config.mongo_users_collection

        self.client = self.get_mongo_client()
        self.db = self.client[self.db_name]
        self.users_collection = self.db[self.users_collection_name]

    def get_mongo_client(
        self,
    ) -> AsyncIOMotorClient:
        # Проверяем, что user и password не пустые и не равны "..."
        has_auth = (
            self.user
            and self.password
            and self.user != "..."
            and self.password != "..."
        )
        
        if has_auth:
            uri = f"mongodb://{self.user}:{self.password}@{self.host}:{self.port}/{self.db_name}"
        else:
            uri = f"mongodb://{self.host}:{self.port}/{self.db_name}"

        return AsyncIOMotorClient(
            uri,
            tls=self.enable_ssl,
        )

    async def ping(
        self,
    ) -> bool:
        """
        Проверяет подключение к MongoDB.
        
        Returns:
            True, если подключение успешно, иначе False
        """
        try:
            await self.client.admin.command(
                "ping",
            )
            return True
        except Exception as e:
            _LOG.error(
                f"Ошибка подключения к MongoDB: {e}",
            )
            return False

    async def get_user(
        self,
        tg_user_id: int,
    ) -> Optional[User]:
        try:
            doc = await self.users_collection.find_one(
                {
                    "id": tg_user_id,
                }
            )
            if not doc:
                return None
            return User(**doc)
        except Exception as e:
            _LOG.error(
                f"Ошибка при получении пользователя {tg_user_id} из MongoDB: {e}"
            )
            return None

    async def create_or_update_user(
        self,
        user: User,
    ) -> User:
        """
        Создает нового пользователя или обновляет существующего.
        Если пользователь существует, обновляет его данные (username, name и т.д.),
        но сохраняет роль и дату создания.
        
        Args:
            user: Объект пользователя для создания/обновления
        
        Returns:
            Созданный или обновленный пользователь
        """
        try:
            existing_user = await self.get_user(user.id)
            
            if existing_user:
                # Обновляем существующего пользователя
                update_data = user.model_dump(
                    exclude={"id", "role", "created_at"},
                )
                update_data["updated_at"] = dt.datetime.now(tz=MOSCOW_TZ)
                
                await self.users_collection.update_one(
                    {"id": user.id},
                    {"$set": update_data},
                )
                
                # Возвращаем обновленного пользователя с сохраненными полями
                updated_user = existing_user.model_copy(
                    update=update_data,
                )
                return updated_user
            else:
                # Создаем нового пользователя
                user_dict = user.model_dump()
                await self.users_collection.insert_one(user_dict)
                _LOG.info(
                    f"Создан новый пользователь: {user.id} ({user.username or 'без username'})",
                )
                return user
        except Exception as e:
            _LOG.error(
                f"Ошибка при создании/обновлении пользователя {user.id} в MongoDB: {e}",
            )
            raise
