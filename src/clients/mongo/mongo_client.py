import logging
from typing import Optional
import datetime as dt

from motor.motor_asyncio import AsyncIOMotorClient

from src.config import MongoConfig
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
)
from src.models.user_roles import UserRole


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
        self.transactions_collection = self.db["transactions"]

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
    
    async def update_user_daily_bonus_date(
        self,
        user_id: int,
        date: dt.date,
    ) -> None:
        """
        Обновляет дату последнего получения ежедневного бонуса.
        
        Args:
            user_id: Telegram user_id пользователя
            date: Дата получения бонуса
        """
        try:
            await self.users_collection.update_one(
                {"id": user_id},
                {"$set": {
                    "last_daily_bonus_date": date,
                    "updated_at": dt.datetime.now(tz=MOSCOW_TZ),
                }},
            )
            _LOG.info(f"Обновлена дата ежедневного бонуса для пользователя {user_id}: {date}")
        except Exception as e:
            _LOG.error(f"Ошибка при обновлении даты ежедневного бонуса для пользователя {user_id}: {e}")
            raise
    
    async def update_user_referral_code(
        self,
        user_id: int,
        referral_code: str,
    ) -> None:
        """
        Обновляет реферальный код пользователя.
        
        Args:
            user_id: Telegram user_id пользователя
            referral_code: Реферальный код
        """
        try:
            await self.users_collection.update_one(
                {"id": user_id},
                {"$set": {
                    "referral_code": referral_code,
                    "updated_at": dt.datetime.now(tz=MOSCOW_TZ),
                }},
            )
            _LOG.info(f"Обновлен реферальный код для пользователя {user_id}: {referral_code}")
        except Exception as e:
            _LOG.error(f"Ошибка при обновлении реферального кода для пользователя {user_id}: {e}")
            raise

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

    async def get_players_rating(
        self,
        filter_type: str = "all_time",
        tournament_id: Optional[str] = None,
        limit: int = 50,
    ) -> list[User]:
        """
        Получает рейтинг игроков с фильтрацией.
        
        Args:
            filter_type: Тип фильтра (all_time, season, month, tournament)
            tournament_id: ID турнира (если filter_type == "tournament")
            limit: Максимальное количество записей
        
        Returns:
            Список пользователей, отсортированный по рейтингу
        """
        try:
            query = {}
            
            # Фильтр по времени (пока упрощенная версия - за всё время)
            # В будущем можно добавить фильтрацию по датам
            if filter_type == "tournament" and tournament_id:
                # Для фильтра по турниру нужно будет получать участников турнира
                # Пока возвращаем общий рейтинг
                pass
            
            # Сортируем по total_kills (основной показатель) по убыванию
            cursor = (
                self.users_collection
                .find(query)
                .sort("total_kills", -1)
                .limit(limit)
            )
            
            players = []
            async for doc in cursor:
                players.append(User(**doc))
            
            return players
        except Exception as e:
            _LOG.error(
                f"Ошибка при получении рейтинга игроков: {e}",
            )
            return []
    
    async def update_user_daily_bonus_date(
        self,
        user_id: int,
        date: dt.date,
    ) -> None:
        """
        Обновляет дату последнего получения ежедневного бонуса.
        
        Args:
            user_id: Telegram user_id пользователя
            date: Дата получения бонуса
        """
        try:
            await self.users_collection.update_one(
                {"id": user_id},
                {"$set": {
                    "last_daily_bonus_date": date,
                    "updated_at": dt.datetime.now(tz=MOSCOW_TZ),
                }},
            )
            _LOG.info(f"Обновлена дата ежедневного бонуса для пользователя {user_id}: {date}")
        except Exception as e:
            _LOG.error(f"Ошибка при обновлении даты ежедневного бонуса для пользователя {user_id}: {e}")
            raise
    
    async def update_user_referral_code(
        self,
        user_id: int,
        referral_code: str,
    ) -> None:
        """
        Обновляет реферальный код пользователя.
        
        Args:
            user_id: Telegram user_id пользователя
            referral_code: Реферальный код
        """
        try:
            await self.users_collection.update_one(
                {"id": user_id},
                {"$set": {
                    "referral_code": referral_code,
                    "updated_at": dt.datetime.now(tz=MOSCOW_TZ),
                }},
            )
            _LOG.info(f"Обновлен реферальный код для пользователя {user_id}: {referral_code}")
        except Exception as e:
            _LOG.error(f"Ошибка при обновлении реферального кода для пользователя {user_id}: {e}")
            raise

    async def get_teams_rating(
        self,
        filter_type: str = "all_time",
        tournament_id: Optional[str] = None,
        limit: int = 50,
    ) -> list[Team]:
        """
        Получает рейтинг команд с фильтрацией.
        
        Args:
            filter_type: Тип фильтра (all_time, season, month, tournament)
            tournament_id: ID турнира (если filter_type == "tournament")
            limit: Максимальное количество записей
        
        Returns:
            Список команд, отсортированный по рейтингу
        """
        try:
            query = {}
            
            # Фильтр по времени (пока упрощенная версия - за всё время)
            if filter_type == "tournament" and tournament_id:
                # Для фильтра по турниру нужно будет получать участников турнира
                # Пока возвращаем общий рейтинг
                pass
            
            # Сортируем по total_points (основной показатель) по убыванию
            cursor = (
                self.teams_collection
                .find(query)
                .sort("total_points", -1)
                .limit(limit)
            )
            
            teams = []
            async for doc in cursor:
                teams.append(Team(**doc))
            
            return teams
        except Exception as e:
            _LOG.error(
                f"Ошибка при получении рейтинга команд: {e}",
            )
            return []
    
    async def update_user_daily_bonus_date(
        self,
        user_id: int,
        date: dt.date,
    ) -> None:
        """
        Обновляет дату последнего получения ежедневного бонуса.
        
        Args:
            user_id: Telegram user_id пользователя
            date: Дата получения бонуса
        """
        try:
            await self.users_collection.update_one(
                {"id": user_id},
                {"$set": {
                    "last_daily_bonus_date": date,
                    "updated_at": dt.datetime.now(tz=MOSCOW_TZ),
                }},
            )
            _LOG.info(f"Обновлена дата ежедневного бонуса для пользователя {user_id}: {date}")
        except Exception as e:
            _LOG.error(f"Ошибка при обновлении даты ежедневного бонуса для пользователя {user_id}: {e}")
            raise
    
    async def update_user_referral_code(
        self,
        user_id: int,
        referral_code: str,
    ) -> None:
        """
        Обновляет реферальный код пользователя.
        
        Args:
            user_id: Telegram user_id пользователя
            referral_code: Реферальный код
        """
        try:
            await self.users_collection.update_one(
                {"id": user_id},
                {"$set": {
                    "referral_code": referral_code,
                    "updated_at": dt.datetime.now(tz=MOSCOW_TZ),
                }},
            )
            _LOG.info(f"Обновлен реферальный код для пользователя {user_id}: {referral_code}")
        except Exception as e:
            _LOG.error(f"Ошибка при обновлении реферального кода для пользователя {user_id}: {e}")
            raise

    async def get_user_rating_position(
        self,
        user_id: int,
        filter_type: str = "all_time",
    ) -> Optional[int]:
        """
        Получает позицию пользователя в рейтинге.
        
        Args:
            user_id: Telegram user_id
            filter_type: Тип фильтра (all_time, season, month, tournament)
        
        Returns:
            Позиция в рейтинге (1-based) или None, если пользователь не найден
        """
        try:
            players = await self.get_players_rating(filter_type=filter_type, limit=1000)
            for idx, player in enumerate(players, start=1):
                if player.id == user_id:
                    return idx
            return None
        except Exception as e:
            _LOG.error(
                f"Ошибка при получении позиции пользователя {user_id} в рейтинге: {e}",
            )
            return None

    async def get_team_rating_position(
        self,
        team_id: str,
        filter_type: str = "all_time",
    ) -> Optional[int]:
        """
        Получает позицию команды в рейтинге.
        
        Args:
            team_id: ID команды
            filter_type: Тип фильтра (all_time, season, month, tournament)
        
        Returns:
            Позиция в рейтинге (1-based) или None, если команда не найдена
        """
        try:
            teams = await self.get_teams_rating(filter_type=filter_type, limit=1000)
            for idx, team in enumerate(teams, start=1):
                if team.id == team_id:
                    return idx
            return None
        except Exception as e:
            _LOG.error(
                f"Ошибка при получении позиции команды {team_id} в рейтинге: {e}",
            )
            return None

    async def get_user_balance(
        self,
        user_id: int,
    ) -> int:
        """
        Получает баланс CD токенов пользователя.
        
        Args:
            user_id: Telegram user_id
        
        Returns:
            Баланс пользователя (по умолчанию 0)
        """
        try:
            user = await self.get_user(user_id)
            if user:
                return user.balance or 0
            return 0
        except Exception as e:
            _LOG.error(
                f"Ошибка при получении баланса пользователя {user_id}: {e}",
            )
            return 0

    async def add_transaction(
        self,
        user_id: int,
        transaction_type: TransactionType,
        amount: int,
        description: str,
    ) -> Transaction:
        """
        Добавляет транзакцию и обновляет баланс пользователя.
        
        Args:
            user_id: Telegram user_id
            transaction_type: Тип транзакции (начисление/списание)
            amount: Сумма транзакции
            description: Описание операции
        
        Returns:
            Созданная транзакция
        """
        try:
            import secrets
            transaction_id = f"tx_{secrets.token_urlsafe(12)}"
            
            # Создаем транзакцию
            transaction = Transaction(
                id=transaction_id,
                user_id=user_id,
                transaction_type=transaction_type,
                amount=amount,
                description=description,
            )
            
            # Сохраняем транзакцию
            await self.transactions_collection.insert_one(transaction.model_dump())
            
            # Обновляем баланс пользователя
            user = await self.get_user(user_id)
            if user:
                if transaction_type == TransactionType.DEPOSIT:
                    new_balance = (user.balance or 0) + amount
                else:  # WITHDRAWAL
                    new_balance = max(0, (user.balance or 0) - amount)
                
                await self.users_collection.update_one(
                    {"id": user_id},
                    {
                        "$set": {
                            "balance": new_balance,
                            "updated_at": dt.datetime.now(tz=MOSCOW_TZ),
                        }
                    },
                )
            else:
                # Если пользователя нет, создаем его с балансом
                if transaction_type == TransactionType.DEPOSIT:
                    new_balance = amount
                else:
                    new_balance = 0
                
                # Создаем базового пользователя (минимальные данные)
                from src.models.user_roles import UserRole
                new_user = User(
                    id=user_id,
                    balance=new_balance,
                    role=UserRole.USER,
                )
                await self.users_collection.insert_one(new_user.model_dump())
            
            _LOG.info(
                f"Транзакция {transaction_id} создана для пользователя {user_id}: "
                f"{transaction_type.value} {amount} CD токенов",
            )
            
            return transaction
        except Exception as e:
            _LOG.error(
                f"Ошибка при создании транзакции для пользователя {user_id}: {e}",
            )
            raise

    async def get_user_transactions(
        self,
        user_id: int,
        limit: int = 20,
    ) -> list[Transaction]:
        """
        Получает историю транзакций пользователя.
        
        Args:
            user_id: Telegram user_id
            limit: Максимальное количество транзакций
        
        Returns:
            Список транзакций (от новых к старым)
        """
        try:
            cursor = (
                self.transactions_collection
                .find({"user_id": user_id})
                .sort("created_at", -1)
                .limit(limit)
            )
            
            transactions = []
            async for doc in cursor:
                transactions.append(Transaction(**doc))
            
            return transactions
        except Exception as e:
            _LOG.error(
                f"Ошибка при получении транзакций пользователя {user_id}: {e}",
            )
            return []
    
    async def update_user_daily_bonus_date(
        self,
        user_id: int,
        date: dt.date,
    ) -> None:
        """
        Обновляет дату последнего получения ежедневного бонуса.
        
        Args:
            user_id: Telegram user_id пользователя
            date: Дата получения бонуса
        """
        try:
            await self.users_collection.update_one(
                {"id": user_id},
                {"$set": {
                    "last_daily_bonus_date": date,
                    "updated_at": dt.datetime.now(tz=MOSCOW_TZ),
                }},
            )
            _LOG.info(f"Обновлена дата ежедневного бонуса для пользователя {user_id}: {date}")
        except Exception as e:
            _LOG.error(f"Ошибка при обновлении даты ежедневного бонуса для пользователя {user_id}: {e}")
            raise
    
    async def update_user_referral_code(
        self,
        user_id: int,
        referral_code: str,
    ) -> None:
        """
        Обновляет реферальный код пользователя.
        
        Args:
            user_id: Telegram user_id пользователя
            referral_code: Реферальный код
        """
        try:
            await self.users_collection.update_one(
                {"id": user_id},
                {"$set": {
                    "referral_code": referral_code,
                    "updated_at": dt.datetime.now(tz=MOSCOW_TZ),
                }},
            )
            _LOG.info(f"Обновлен реферальный код для пользователя {user_id}: {referral_code}")
        except Exception as e:
            _LOG.error(f"Ошибка при обновлении реферального кода для пользователя {user_id}: {e}")
            raise


    async def find_user_by_username_or_nickname(
        self,
        query: str,
    ) -> Optional[User]:
        """
        Ищет пользователя по username или nickname.
        
        Args:
            query: Поисковый запрос (username или nickname)
        
        Returns:
            Найденный пользователь или None
        """
        try:
            # Ищем по username (без @)
            doc = await self.users_collection.find_one(
                {"username": query}
            )
            if doc:
                return User(**doc)
            
            # Ищем по nickname
            doc = await self.users_collection.find_one(
                {"nickname": query}
            )
            if doc:
                return User(**doc)
            
            return None
        except Exception as e:
            _LOG.error(f"Ошибка при поиске пользователя по запросу '{query}': {e}")
            return None
    
    async def update_user_ban_status(
        self,
        user_id: int,
        is_banned: bool,
    ) -> None:
        """
        Обновляет статус бана пользователя.
        
        Args:
            user_id: Telegram user_id пользователя
            is_banned: Забанен ли пользователь
        """
        try:
            await self.users_collection.update_one(
                {"id": user_id},
                {"$set": {
                    "is_banned": is_banned,
                    "updated_at": dt.datetime.now(tz=MOSCOW_TZ),
                }},
            )
            _LOG.info(f"Обновлен статус бана для пользователя {user_id}: {is_banned}")
        except Exception as e:
            _LOG.error(f"Ошибка при обновлении статуса бана для пользователя {user_id}: {e}")
            raise
    
    async def update_user_role(
        self,
        user_id: int,
        role: UserRole,
    ) -> None:
        """
        Обновляет роль пользователя.
        
        Args:
            user_id: Telegram user_id пользователя
            role: Новая роль пользователя
        """
        try:
            await self.users_collection.update_one(
                {"id": user_id},
                {"$set": {
                    "role": role.value,
                    "updated_at": dt.datetime.now(tz=MOSCOW_TZ),
                }},
            )
            _LOG.info(f"Обновлена роль пользователя {user_id}: {role.value}")
        except Exception as e:
            _LOG.error(f"Ошибка при обновлении роли пользователя {user_id}: {e}")
            raise

    async def find_team_by_name_or_tag(
        self,
        query: str,
    ) -> Optional[Team]:
        """
        Ищет команду по названию или тегу.
        
        Args:
            query: Поисковый запрос (название или тег)
        
        Returns:
            Найденная команда или None
        """
        try:
            # Ищем по названию
            doc = await self.teams_collection.find_one(
                {"name": query}
            )
            if doc:
                return Team(**doc)
            
            # Ищем по тегу
            doc = await self.teams_collection.find_one(
                {"tag": query}
            )
            if doc:
                return Team(**doc)
            
            return None
        except Exception as e:
            _LOG.error(f"Ошибка при поиске команды по запросу '{query}': {e}")
            return None
    
    async def update_team_ban_status(
        self,
        team_id: str,
        is_banned: bool,
    ) -> None:
        """
        Обновляет статус бана команды.
        
        Args:
            team_id: ID команды
            is_banned: Забанена ли команда
        """
        try:
            await self.teams_collection.update_one(
                {"id": team_id},
                {"$set": {
                    "is_banned": is_banned,
                    "updated_at": dt.datetime.now(tz=MOSCOW_TZ),
                }},
            )
            _LOG.info(f"Обновлен статус бана для команды {team_id}: {is_banned}")
        except Exception as e:
            _LOG.error(f"Ошибка при обновлении статуса бана для команды {team_id}: {e}")
            raise
    
    async def update_team_captain_confirmed(
        self,
        team_id: str,
        captain_confirmed: bool,
    ) -> None:
        """
        Обновляет статус подтверждения капитана команды.
        
        Args:
            team_id: ID команды
            captain_confirmed: Подтвержден ли капитан
        """
        try:
            await self.teams_collection.update_one(
                {"id": team_id},
                {"$set": {
                    "captain_confirmed": captain_confirmed,
                    "updated_at": dt.datetime.now(tz=MOSCOW_TZ),
                }},
            )
            _LOG.info(f"Обновлен статус подтверждения капитана для команды {team_id}: {captain_confirmed}")
        except Exception as e:
            _LOG.error(f"Ошибка при обновлении статуса подтверждения капитана для команды {team_id}: {e}")
            raise

    async def get_rating_rules(
        self,
    ) -> Optional[RatingRules]:
        """
        Получает правила расчета рейтинга.
        
        Returns:
            Объект правил рейтинга или None
        """
        try:
            # Используем отдельную коллекцию для правил рейтинга
            # Или можно хранить в отдельной коллекции settings
            doc = await self.users_collection.find_one({"id": "rating_rules"})
            if not doc:
                # Создаем правила по умолчанию
                default_rules = RatingRules()
                await self.users_collection.insert_one(default_rules.model_dump())
                return default_rules
            return RatingRules(**doc)
        except Exception as e:
            _LOG.error(f"Ошибка при получении правил рейтинга: {e}")
            # Возвращаем правила по умолчанию
            return RatingRules()
    
    async def update_rating_metric(
        self,
        rating_type: str,
        metric: RatingMetric,
    ) -> None:
        """
        Обновляет метрику для рейтинга.
        
        Args:
            rating_type: Тип рейтинга (player или team)
            metric: Новая метрика
        """
        try:
            update_data = {
                "updated_at": dt.datetime.now(tz=MOSCOW_TZ),
            }
            
            if rating_type == "player":
                update_data["player_metric"] = metric.value
            elif rating_type == "team":
                update_data["team_metric"] = metric.value
            
            settings_collection = self.db["settings"]
            await settings_collection.update_one(
                {"id": "rating_rules"},
                {"$set": update_data},
                upsert=True,
            )
            _LOG.info(f"Обновлена метрика рейтинга {rating_type}: {metric.value}")
        except Exception as e:
            _LOG.error(f"Ошибка при обновлении метрики рейтинга: {e}")
            raise
    
    async def recalculate_ratings(
        self,
    ) -> None:
        """
        Пересчитывает рейтинг всех игроков и команд на основе результатов турниров.
        """
        try:
            # Получаем правила рейтинга
            rules = await self.get_rating_rules()
            
            # Получаем все опубликованные результаты турниров
            tournament_results_collection = self.db["tournament_results"]
            cursor = tournament_results_collection.find({"is_published": True})
            
            # Собираем статистику по игрокам и командам
            player_stats: dict[int, dict[str, int]] = {}  # {user_id: {"kills": int, "points": int}}
            team_stats: dict[str, dict[str, int]] = {}  # {team_id: {"kills": int, "points": int}}
            
            async for doc in cursor:
                result = TournamentResult(**doc)
                if result.player_id:
                    if result.player_id not in player_stats:
                        player_stats[result.player_id] = {"kills": 0, "points": 0}
                    player_stats[result.player_id]["kills"] += result.total_kills
                    player_stats[result.player_id]["points"] += result.total_points
                elif result.team_id:
                    if result.team_id not in team_stats:
                        team_stats[result.team_id] = {"kills": 0, "points": 0}
                    team_stats[result.team_id]["kills"] += result.total_kills
                    team_stats[result.team_id]["points"] += result.total_points
            
            # Пересчитываем рейтинг игроков
            players = []
            cursor = self.users_collection.find({})
            async for doc in cursor:
                if "id" in doc and isinstance(doc["id"], int):
                    try:
                        user = User(**doc)
                        # Обновляем статистику из результатов турниров
                        if user.id in player_stats:
                            user.total_kills = player_stats[user.id]["kills"]
                            # Обновляем в БД
                            await self.users_collection.update_one(
                                {"id": user.id},
                                {"$set": {"total_kills": user.total_kills}},
                            )
                        players.append(user)
                    except Exception:
                        continue
            
            # Сортируем игроков по метрике
            if rules.player_metric == RatingMetric.KILLS:
                players.sort(key=lambda p: p.total_kills or 0, reverse=True)
            else:
                # Если метрика - очки, используем points из статистики
                players.sort(
                    key=lambda p: player_stats.get(p.id, {}).get("points", 0),
                    reverse=True,
                )
            
            # Обновляем позиции в рейтинге
            for idx, player in enumerate(players, start=1):
                await self.users_collection.update_one(
                    {"id": player.id},
                    {"$set": {"rating_position": idx}},
                )
            
            # Пересчитываем рейтинг команд
            teams = []
            cursor = self.teams_collection.find({})
            async for doc in cursor:
                try:
                    team = Team(**doc)
                    # Обновляем статистику из результатов турниров
                    if team.id in team_stats:
                        # Обновляем в БД (если есть поле total_kills для команд)
                        await self.teams_collection.update_one(
                            {"id": team.id},
                            {"$set": {"total_points": team_stats[team.id]["points"]}},
                        )
                        team.total_points = team_stats[team.id]["points"]
                    teams.append(team)
                except Exception:
                    continue
            
            # Сортируем команды по метрике
            if rules.team_metric == RatingMetric.POINTS:
                teams.sort(key=lambda t: t.total_points or 0, reverse=True)
            else:
                # Если метрика - киллы, используем kills из статистики
                teams.sort(
                    key=lambda t: team_stats.get(t.id, {}).get("kills", 0),
                    reverse=True,
                )
            
            # Обновляем позиции в рейтинге
            for idx, team in enumerate(teams, start=1):
                await self.teams_collection.update_one(
                    {"id": team.id},
                    {"$set": {"rating_position": idx}},
                )
            
            _LOG.info("Рейтинг успешно пересчитан на основе результатов турниров")
        except Exception as e:
            _LOG.error(f"Ошибка при пересчёте рейтинга: {e}")
            raise

    async def get_tournament_matches(
        self,
        tournament_id: str,
    ) -> list[Match]:
        """
        Получает список матчей турнира.
        
        Args:
            tournament_id: ID турнира
        
        Returns:
            Список матчей
        """
        try:
            matches_collection = self.db["matches"]
            cursor = matches_collection.find({"tournament_id": tournament_id})
            matches = []
            async for doc in cursor:
                matches.append(Match(**doc))
            return matches
        except Exception as e:
            _LOG.error(f"Ошибка при получении матчей турнира {tournament_id}: {e}")
            return []
    
    async def get_match(
        self,
        match_id: str,
    ) -> Optional[Match]:
        """
        Получает матч по ID.
        
        Args:
            match_id: ID матча
        
        Returns:
            Объект матча или None
        """
        try:
            matches_collection = self.db["matches"]
            doc = await matches_collection.find_one({"id": match_id})
            if not doc:
                return None
            return Match(**doc)
        except Exception as e:
            _LOG.error(f"Ошибка при получении матча {match_id}: {e}")
            return None
    
    async def create_match(
        self,
        tournament_id: str,
        name: str,
        round_number: Optional[int] = None,
    ) -> Match:
        """
        Создает новый матч в турнире.
        
        Args:
            tournament_id: ID турнира
            name: Название матча
            round_number: Номер раунда (опционально)
        
        Returns:
            Созданный матч
        """
        try:
            import secrets
            match_id = f"match_{secrets.token_urlsafe(12)}"
            match = Match(
                id=match_id,
                tournament_id=tournament_id,
                name=name,
                round_number=round_number,
            )
            matches_collection = self.db["matches"]
            await matches_collection.insert_one(match.model_dump())
            _LOG.info(f"Создан матч {match_id} в турнире {tournament_id}")
            return match
        except Exception as e:
            _LOG.error(f"Ошибка при создании матча: {e}")
            raise
    
    async def save_match_result(
        self,
        match_id: str,
        tournament_id: str,
        participant_id: int | str,
        is_solo: bool,
        kills: int,
    ) -> None:
        """
        Сохраняет результат матча.
        
        Args:
            match_id: ID матча
            tournament_id: ID турнира
            participant_id: ID участника (user_id или team_id)
            is_solo: Соло турнир или командный
            kills: Количество киллов
        """
        try:
            import secrets
            result_id = f"match_result_{secrets.token_urlsafe(12)}"
            match_results_collection = self.db["match_results"]
            
            result = MatchResult(
                id=result_id,
                match_id=match_id,
                tournament_id=tournament_id,
                player_id=int(participant_id) if is_solo else None,
                team_id=str(participant_id) if not is_solo else None,
                kills=kills,
            )
            
            await match_results_collection.insert_one(result.model_dump())
            _LOG.info(f"Сохранен результат матча {match_id} для участника {participant_id}: {kills} киллов")
        except Exception as e:
            _LOG.error(f"Ошибка при сохранении результата матча: {e}")
            raise
    
    async def complete_match(
        self,
        match_id: str,
    ) -> None:
        """
        Отмечает матч как завершенный.
        
        Args:
            match_id: ID матча
        """
        try:
            matches_collection = self.db["matches"]
            await matches_collection.update_one(
                {"id": match_id},
                {"$set": {
                    "is_completed": True,
                    "updated_at": dt.datetime.now(tz=MOSCOW_TZ),
                }},
            )
            _LOG.info(f"Матч {match_id} завершен")
        except Exception as e:
            _LOG.error(f"Ошибка при завершении матча: {e}")
            raise
    
    async def save_tournament_result(
        self,
        tournament_id: str,
        participant_id: int | str,
        is_solo: bool,
        total_kills: int,
    ) -> None:
        """
        Сохраняет итоговый результат турнира для участника.
        
        Args:
            tournament_id: ID турнира
            participant_id: ID участника (user_id или team_id)
            is_solo: Соло турнир или командный
            total_kills: Общее количество киллов
        """
        try:
            import secrets
            result_id = f"tournament_result_{secrets.token_urlsafe(12)}"
            tournament_results_collection = self.db["tournament_results"]
            
            # Проверяем, есть ли уже результат
            query = {
                "tournament_id": tournament_id,
            }
            if is_solo:
                query["player_id"] = int(participant_id)
            else:
                query["team_id"] = str(participant_id)
            
            existing = await tournament_results_collection.find_one(query)
            
            if existing:
                # Обновляем существующий результат
                await tournament_results_collection.update_one(
                    query,
                    {"$set": {
                        "total_kills": total_kills,
                        "updated_at": dt.datetime.now(tz=MOSCOW_TZ),
                    }},
                )
            else:
                # Создаем новый результат
                result = TournamentResult(
                    id=result_id,
                    tournament_id=tournament_id,
                    player_id=int(participant_id) if is_solo else None,
                    team_id=str(participant_id) if not is_solo else None,
                    total_kills=total_kills,
                )
                await tournament_results_collection.insert_one(result.model_dump())
            
            _LOG.info(f"Сохранен результат турнира {tournament_id} для участника {participant_id}: {total_kills} киллов")
        except Exception as e:
            _LOG.error(f"Ошибка при сохранении результата турнира: {e}")
            raise
    
    async def get_tournament_results(
        self,
        tournament_id: str,
    ) -> list[TournamentResult]:
        """
        Получает результаты турнира.
        
        Args:
            tournament_id: ID турнира
        
        Returns:
            Список результатов
        """
        try:
            tournament_results_collection = self.db["tournament_results"]
            cursor = tournament_results_collection.find({"tournament_id": tournament_id})
            results = []
            async for doc in cursor:
                results.append(TournamentResult(**doc))
            return results
        except Exception as e:
            _LOG.error(f"Ошибка при получении результатов турнира {tournament_id}: {e}")
            return []
    
    async def update_tournament_result_position(
        self,
        result_id: str,
        position: int,
    ) -> None:
        """
        Обновляет позицию в результатах турнира.
        
        Args:
            result_id: ID результата
            position: Позиция
        """
        try:
            tournament_results_collection = self.db["tournament_results"]
            await tournament_results_collection.update_one(
                {"id": result_id},
                {"$set": {"position": position}},
            )
        except Exception as e:
            _LOG.error(f"Ошибка при обновлении позиции результата: {e}")
            raise
    
    async def update_tournament_results_from_matches(
        self,
        tournament_id: str,
    ) -> None:
        """
        Обновляет итоговые результаты турнира на основе результатов матчей.
        
        Args:
            tournament_id: ID турнира
        """
        try:
            match_results_collection = self.db["match_results"]
            tournament_results_collection = self.db["tournament_results"]
            
            # Получаем все результаты матчей турнира
            cursor = match_results_collection.find({"tournament_id": tournament_id})
            
            # Группируем по участникам
            participant_kills: dict[tuple[str, Optional[int], Optional[str]], int] = {}
            
            async for doc in cursor:
                result = MatchResult(**doc)
                key = (tournament_id, result.player_id, result.team_id)
                participant_kills[key] = participant_kills.get(key, 0) + result.kills
            
            # Обновляем или создаем итоговые результаты
            for (tid, player_id, team_id), total_kills in participant_kills.items():
                query = {"tournament_id": tid}
                if player_id:
                    query["player_id"] = player_id
                if team_id:
                    query["team_id"] = team_id
                
                existing = await tournament_results_collection.find_one(query)
                if existing:
                    await tournament_results_collection.update_one(
                        query,
                        {"$set": {
                            "total_kills": total_kills,
                            "updated_at": dt.datetime.now(tz=MOSCOW_TZ),
                        }},
                    )
                else:
                    import secrets
                    result_id = f"tournament_result_{secrets.token_urlsafe(12)}"
                    result = TournamentResult(
                        id=result_id,
                        tournament_id=tid,
                        player_id=player_id,
                        team_id=team_id,
                        total_kills=total_kills,
                    )
                    await tournament_results_collection.insert_one(result.model_dump())
            
            _LOG.info(f"Обновлены итоговые результаты турнира {tournament_id} на основе матчей")
        except Exception as e:
            _LOG.error(f"Ошибка при обновлении результатов турнира из матчей: {e}")
            raise
    
    async def publish_tournament_results(
        self,
        tournament_id: str,
    ) -> None:
        """
        Публикует результаты турнира.
        
        Args:
            tournament_id: ID турнира
        """
        try:
            # Обновляем статус результатов
            tournament_results_collection = self.db["tournament_results"]
            await tournament_results_collection.update_many(
                {"tournament_id": tournament_id},
                {"$set": {"is_published": True}},
            )
            
            # Обновляем статус турнира
            await self.tournaments_collection.update_one(
                {"id": tournament_id},
                {"$set": {
                    "results_published": True,
                    "updated_at": dt.datetime.now(tz=MOSCOW_TZ),
                }},
            )
            
            _LOG.info(f"Результаты турнира {tournament_id} опубликованы")
        except Exception as e:
            _LOG.error(f"Ошибка при публикации результатов турнира: {e}")
            raise
