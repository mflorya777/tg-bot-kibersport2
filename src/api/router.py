from typing import Optional
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from src.clients.mongo import MongoClient


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
