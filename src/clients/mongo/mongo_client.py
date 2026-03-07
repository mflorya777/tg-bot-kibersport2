import logging
from typing import Optional
import datetime as dt

from motor.motor_asyncio import AsyncIOMotorClient

from src.config import MongoConfig
from src.models.mongo_models import User, Team, Tournament, TournamentStatus, TournamentFormat


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
        self.teams_collection = self.db["teams"]
        self.tournaments_collection = self.db["tournaments"]

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

    async def get_team(
        self,
        team_id: str,
    ) -> Optional[Team]:
        """
        Получает команду по ID.
        
        Args:
            team_id: ID команды
        
        Returns:
            Объект команды или None, если команда не найдена
        """
        try:
            doc = await self.teams_collection.find_one({"id": team_id})
            if not doc:
                return None
            return Team(**doc)
        except Exception as e:
            _LOG.error(
                f"Ошибка при получении команды {team_id} из MongoDB: {e}",
            )
            return None

    async def get_user_team(
        self,
        user_id: int,
    ) -> Optional[Team]:
        """
        Получает команду пользователя.
        
        Args:
            user_id: Telegram user_id
        
        Returns:
            Объект команды или None, если пользователь не в команде
        """
        try:
            user = await self.get_user(user_id)
            if not user or not user.team_id:
                return None
            return await self.get_team(user.team_id)
        except Exception as e:
            _LOG.error(
                f"Ошибка при получении команды пользователя {user_id}: {e}",
            )
            return None

    async def create_team(
        self,
        team: Team,
    ) -> Team:
        """
        Создает новую команду в базе данных.
        
        Args:
            team: Объект команды для создания
        
        Returns:
            Созданная команда
        """
        try:
            team_dict = team.model_dump()
            await self.teams_collection.insert_one(team_dict)
            _LOG.info(
                f"Создана новая команда: {team.id} ({team.name})",
            )
            return team
        except Exception as e:
            _LOG.error(
                f"Ошибка при создании команды {team.id} в MongoDB: {e}",
            )
            raise

    async def update_user_team(
        self,
        user_id: int,
        team_id: Optional[str],
    ) -> None:
        """
        Обновляет team_id пользователя.
        
        Args:
            user_id: Telegram user_id
            team_id: ID команды (None для удаления из команды)
        """
        try:
            update_data = {
                "team_id": team_id,
                "updated_at": dt.datetime.now(tz=MOSCOW_TZ),
            }
            await self.users_collection.update_one(
                {"id": user_id},
                {"$set": update_data},
            )
        except Exception as e:
            _LOG.error(
                f"Ошибка при обновлении team_id пользователя {user_id}: {e}",
            )
            raise

    async def get_tournament(
        self,
        tournament_id: str,
    ) -> Optional[Tournament]:
        """
        Получает турнир по ID.
        
        Args:
            tournament_id: ID турнира
        
        Returns:
            Объект турнира или None, если турнир не найден
        """
        try:
            doc = await self.tournaments_collection.find_one({"id": tournament_id})
            if not doc:
                return None
            return Tournament(**doc)
        except Exception as e:
            _LOG.error(
                f"Ошибка при получении турнира {tournament_id} из MongoDB: {e}",
            )
            return None

    async def get_tournaments(
        self,
        status: Optional[TournamentStatus] = None,
        game_discipline: Optional[str] = None,
    ) -> list[Tournament]:
        """
        Получает список турниров с фильтрацией.
        
        Args:
            status: Фильтр по статусу (опционально)
            game_discipline: Фильтр по игре/дисциплине (опционально)
        
        Returns:
            Список турниров
        """
        try:
            query = {}
            if status:
                query["status"] = status.value
            if game_discipline:
                query["game_discipline"] = game_discipline
            
            cursor = self.tournaments_collection.find(query).sort("created_at", -1)
            tournaments = []
            async for doc in cursor:
                tournaments.append(Tournament(**doc))
            return tournaments
        except Exception as e:
            _LOG.error(
                f"Ошибка при получении турниров из MongoDB: {e}",
            )
            return []

    async def update_tournament(
        self,
        tournament: Tournament,
    ) -> Tournament:
        """
        Обновляет турнир в базе данных.
        
        Args:
            tournament: Объект турнира для обновления
        
        Returns:
            Обновленный объект турнира
        """
        try:
            tournament.updated_at = dt.datetime.now(tz=MOSCOW_TZ)
            await self.tournaments_collection.update_one(
                {"id": tournament.id},
                {"$set": tournament.model_dump()},
            )
            return tournament
        except Exception as e:
            _LOG.error(
                f"Ошибка при обновлении турнира {tournament.id} в MongoDB: {e}",
            )
            raise

    async def create_tournament(
        self,
        tournament: Tournament,
    ) -> Tournament:
        """
        Создает новый турнир в базе данных.
        
        Args:
            tournament: Объект турнира для создания
        
        Returns:
            Созданный объект турнира
        """
        try:
            await self.tournaments_collection.insert_one(tournament.model_dump())
            return tournament
        except Exception as e:
            _LOG.error(
                f"Ошибка при создании турнира {tournament.id} в MongoDB: {e}",
            )
            raise
