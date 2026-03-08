from typing import Optional, List
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
import datetime as dt
import secrets
import string

from src.clients.mongo import MongoClient
from src.models.mongo_models import (
    GiveawayStatus,
    GiveawayParticipationType,
    TransactionType,
    MOSCOW_TZ,
)
from src.config import BOT_USERNAME


router = APIRouter(prefix="/api", tags=["api"])

# Глобальный экземпляр MongoClient (будет установлен при запуске)
_mongo_client: Optional[MongoClient] = None


def set_mongo_client(client: MongoClient) -> None:
    """
    Устанавливает глобальный экземпляр MongoClient для API.
    
    Args:
        client: Экземпляр MongoClient
    """
    global _mongo_client
    _mongo_client = client


class ProfileResponse(BaseModel):
    """Модель ответа для профиля пользователя."""
    user_id: int
    nickname: Optional[str] = None
    game_discipline: Optional[str] = None
    region_country: Optional[str] = None
    tournaments_played: int = 0
    total_kills: int = 0
    rating_position: Optional[int] = None
    team_name: Optional[str] = None
    team_tag: Optional[str] = None
    balance: int = 0


@router.get("/profile/{user_id}")
async def get_profile(
    user_id: int,
    x_init_data: Optional[str] = Header(None, alias="X-Init-Data"),
) -> ProfileResponse:
    """
    Получает данные профиля пользователя.
    
    Args:
        user_id: Telegram user_id пользователя
        x_init_data: InitData из Telegram WebApp (для проверки подлинности, опционально)
    
    Returns:
        Данные профиля пользователя
    
    Raises:
        HTTPException: Если пользователь не найден или произошла ошибка
    """
    if _mongo_client is None:
        raise HTTPException(
            status_code=503,
            detail="База данных недоступна",
        )
    
    try:
        # Получаем пользователя из БД
        user = await _mongo_client.get_user(user_id)
        
        if user is None:
            raise HTTPException(
                status_code=404,
                detail="Пользователь не найден",
            )
        
        # Получаем название команды, если пользователь в команде
        team_name = None
        team_tag = None
        if user.team_id:
            team = await _mongo_client.get_team(user.team_id)
            if team:
                team_name = team.name
                team_tag = team.tag
        
        return ProfileResponse(
            user_id=user.id,
            nickname=user.nickname,
            game_discipline=user.game_discipline,
            region_country=user.region_country,
            tournaments_played=user.tournaments_played,
            total_kills=user.total_kills,
            rating_position=user.rating_position,
            team_name=team_name,
            team_tag=team_tag,
            balance=user.balance,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении профиля: {str(e)}",
        )


class PromotionItem(BaseModel):
    """Модель элемента розыгрыша для ответа."""
    id: str
    name: str
    description: str
    start_date: str  # ISO format
    end_date: str  # ISO format
    participation_type: str  # "tokens" or "condition"
    ticket_cost: Optional[int] = None
    condition_description: Optional[str] = None
    ticket_limit_per_user: Optional[int] = None
    status: str  # "draft", "active", "completed"
    user_tickets: int = 0
    winners: Optional[List[dict]] = None


class PromotionsResponse(BaseModel):
    """Модель ответа для списка розыгрышей."""
    promotions: List[PromotionItem]


class BuyTicketRequest(BaseModel):
    """Модель запроса на покупку билета."""
    giveaway_id: str


class BuyTicketResponse(BaseModel):
    """Модель ответа на покупку билета."""
    success: bool
    message: str
    new_balance: int
    tickets_count: int


@router.get("/promotions/{user_id}")
async def get_promotions(
    user_id: int,
    x_init_data: Optional[str] = Header(None, alias="X-Init-Data"),
) -> PromotionsResponse:
    """
    Получает список активных розыгрышей с информацией о билетах пользователя.
    
    Args:
        user_id: Telegram user_id пользователя
        x_init_data: InitData из Telegram WebApp (для проверки подлинности, опционально)
    
    Returns:
        Список розыгрышей с информацией о билетах пользователя
    
    Raises:
        HTTPException: Если произошла ошибка
    """
    if _mongo_client is None:
        raise HTTPException(
            status_code=503,
            detail="База данных недоступна",
        )
    
    try:
        # Получаем все розыгрыши
        giveaways = await _mongo_client.get_giveaways()
        
        # Фильтруем только активные и завершенные (не черновики)
        active_giveaways = [
            g for g in giveaways
            if g.status in (GiveawayStatus.ACTIVE, GiveawayStatus.COMPLETED)
        ]
        
        # Формируем ответ с информацией о билетах пользователя
        promotions = []
        for giveaway in active_giveaways:
            # Получаем количество билетов пользователя
            user_tickets = giveaway.participants.get(user_id, 0)
            
            # Формируем список победителей с именами
            winners_list = None
            if giveaway.winners:
                winners_list = []
                for winner_id in giveaway.winners:
                    winner_user = await _mongo_client.get_user(winner_id)
                    if winner_user:
                        winner_name = winner_user.nickname or winner_user.name or f"ID: {winner_id}"
                        winners_list.append({
                            "id": winner_id,
                            "name": winner_name,
                        })
                    else:
                        winners_list.append({
                            "id": winner_id,
                            "name": f"ID: {winner_id}",
                        })
            
            promotions.append(PromotionItem(
                id=giveaway.id,
                name=giveaway.name,
                description=giveaway.description,
                start_date=giveaway.start_date.isoformat(),
                end_date=giveaway.end_date.isoformat(),
                participation_type=giveaway.participation_type.value,
                ticket_cost=giveaway.ticket_cost,
                condition_description=giveaway.condition_description,
                ticket_limit_per_user=giveaway.ticket_limit_per_user,
                status=giveaway.status.value,
                user_tickets=user_tickets,
                winners=winners_list,
            ))
        
        return PromotionsResponse(promotions=promotions)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении розыгрышей: {str(e)}",
        )


@router.post("/promotions/{user_id}/buy-ticket")
async def buy_ticket(
    user_id: int,
    request: BuyTicketRequest,
    x_init_data: Optional[str] = Header(None, alias="X-Init-Data"),
) -> BuyTicketResponse:
    """
    Покупает билет на розыгрыш.
    
    Args:
        user_id: Telegram user_id пользователя
        request: Запрос с ID розыгрыша
        x_init_data: InitData из Telegram WebApp (для проверки подлинности, опционально)
    
    Returns:
        Результат покупки билета
    
    Raises:
        HTTPException: Если произошла ошибка
    """
    if _mongo_client is None:
        raise HTTPException(
            status_code=503,
            detail="База данных недоступна",
        )
    
    try:
        # Получаем розыгрыш
        giveaway = await _mongo_client.get_giveaway(request.giveaway_id)
        if not giveaway:
            raise HTTPException(
                status_code=404,
                detail="Розыгрыш не найден",
            )
        
        # Проверяем, что розыгрыш активен
        if giveaway.status != GiveawayStatus.ACTIVE:
            raise HTTPException(
                status_code=400,
                detail="Розыгрыш не активен",
            )
        
        # Проверяем, что розыгрыш еще не закончился
        now = dt.datetime.now(tz=MOSCOW_TZ)
        if giveaway.end_date < now:
            raise HTTPException(
                status_code=400,
                detail="Розыгрыш уже завершен",
            )
        
        # Проверяем тип участия
        if giveaway.participation_type != GiveawayParticipationType.TOKENS:
            raise HTTPException(
                status_code=400,
                detail="Этот розыгрыш не требует покупки билетов",
            )
        
        if not giveaway.ticket_cost:
            raise HTTPException(
                status_code=400,
                detail="Стоимость билета не указана",
            )
        
        # Получаем пользователя
        user = await _mongo_client.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="Пользователь не найден",
            )
        
        # Проверяем баланс
        if user.balance < giveaway.ticket_cost:
            raise HTTPException(
                status_code=400,
                detail=f"Недостаточно CD токенов. Требуется: {giveaway.ticket_cost}, доступно: {user.balance}",
            )
        
        # Проверяем лимит билетов
        current_tickets = giveaway.participants.get(user_id, 0)
        if giveaway.ticket_limit_per_user and current_tickets >= giveaway.ticket_limit_per_user:
            raise HTTPException(
                status_code=400,
                detail=f"Достигнут лимит билетов: {giveaway.ticket_limit_per_user}",
            )
        
        # Списываем токены
        await _mongo_client.add_transaction(
            user_id=user_id,
            transaction_type=TransactionType.WITHDRAWAL,
            amount=giveaway.ticket_cost,
            description=f"Покупка билета на розыгрыш '{giveaway.name}'",
        )
        
        # Добавляем билет пользователю
        giveaways_collection = _mongo_client.db["giveaways"]
        new_ticket_count = current_tickets + 1
        
        # Обновляем участников
        participants = giveaway.participants.copy()
        participants[user_id] = new_ticket_count
        
        await giveaways_collection.update_one(
            {"id": request.giveaway_id},
            {"$set": {
                "participants": participants,
                "updated_at": dt.datetime.now(tz=MOSCOW_TZ),
            }},
        )
        
        # Получаем обновленный баланс
        updated_user = await _mongo_client.get_user(user_id)
        new_balance = updated_user.balance if updated_user else 0
        
        return BuyTicketResponse(
            success=True,
            message=f"Билет успешно приобретен за {giveaway.ticket_cost} CD токенов",
            new_balance=new_balance,
            tickets_count=new_ticket_count,
        )
    except HTTPException:
        raise
    except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при покупке билета: {str(e)}",
            )


class ReferralResponse(BaseModel):
    """Модель ответа для реферальной системы."""
    referral_link: str
    referral_code: str
    invited_count: int = 0
    bonus_amount: int = 0
    bonus_per_referral: int = 50
    referral_condition: str = "registration"
    anti_fraud_rule: str = "one_account_one_device"


@router.get("/referral/{user_id}")
async def get_referral(
    user_id: int,
    x_init_data: Optional[str] = Header(None, alias="X-Init-Data"),
) -> ReferralResponse:
    """
    Получает данные реферальной системы для пользователя.
    
    Args:
        user_id: Telegram user_id пользователя
        x_init_data: InitData из Telegram WebApp (для проверки подлинности, опционально)
    
    Returns:
        Данные реферальной системы
    
    Raises:
        HTTPException: Если произошла ошибка
    """
    if _mongo_client is None:
        raise HTTPException(
            status_code=503,
            detail="База данных недоступна",
        )
    
    try:
        # Получаем пользователя из БД
        user = await _mongo_client.get_user(user_id)
        
        if user is None:
            raise HTTPException(
                status_code=404,
                detail="Пользователь не найден",
            )
        
        # Получаем настройки реферальной системы
        referral_settings = await _mongo_client.get_referral_settings()
        if not referral_settings:
            # Используем значения по умолчанию
            bonus_per_referral = 50
            referral_condition = "registration"
            anti_fraud_rule = "one_account_one_device"
        else:
            bonus_per_referral = referral_settings.bonus_per_referral
            referral_condition = referral_settings.referral_condition
            anti_fraud_rule = referral_settings.anti_fraud_rule
        
        # Генерируем или получаем реферальный код
        referral_code = user.referral_code
        if not referral_code:
            # Генерируем реферальный код, если его нет
            # Создаем код из 8 символов (буквы и цифры)
            alphabet = string.ascii_uppercase + string.digits
            referral_code = ''.join(secrets.choice(alphabet) for _ in range(8))
            
            # Сохраняем код в БД
            await _mongo_client.update_user_referral_code(user_id, referral_code)
        
        # Формируем реферальную ссылку
        # Используем имя бота из конфига
        referral_link = f"https://t.me/{BOT_USERNAME}?start={referral_code}"
        
        # Вычисляем общую сумму начисленных бонусов
        # Это количество приглашенных друзей * бонус за каждого
        bonus_amount = user.referrals_count * bonus_per_referral
        
        return ReferralResponse(
            referral_link=referral_link,
            referral_code=referral_code,
            invited_count=user.referrals_count,
            bonus_amount=bonus_amount,
            bonus_per_referral=bonus_per_referral,
            referral_condition=referral_condition,
            anti_fraud_rule=anti_fraud_rule,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении данных реферальной системы: {str(e)}",
        )
