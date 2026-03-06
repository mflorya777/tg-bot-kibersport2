import logging
import secrets
import string
from typing import Optional
from aiogram import types
from aiogram.filters import Command

from src.modules.keyboards import (
    get_main_menu_keyboard,
    get_admin_panel_keyboard,
    get_profile_keyboard,
    get_team_no_team_keyboard,
    get_team_keyboard,
)
from src.models.user_roles import UserRole
from src.models.mongo_models import User, Team
from src.clients.mongo import MongoClient


# Глобальный экземпляр MongoClient (устанавливается при запуске приложения)
_mongo_client: Optional[MongoClient] = None

_LOG = logging.getLogger("kibersport-tg-bot")

# Словарь для хранения состояния ожидания данных команды
_waiting_team_data: dict[int, bool] = {}


def generate_team_id() -> str:
    """
    Генерирует уникальный ID команды.
    
    Returns:
        Уникальный ID команды
    """
    return f"team_{secrets.token_urlsafe(12)}"


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
        await callback.answer("Профиль")
        
        # Получаем данные пользователя из БД
        user = None
        if _mongo_client is not None:
            try:
                user = await _mongo_client.get_user(callback.from_user.id)
            except Exception as e:
                _LOG.error(
                    f"Ошибка при получении профиля пользователя {callback.from_user.id}: {e}",
                )
        
        # Формируем текст профиля
        profile_text = format_profile_text(user, callback.from_user)
        
        await callback.message.edit_text(
            text=profile_text,
            reply_markup=get_profile_keyboard(),
        )
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
        await callback.message.edit_text(
            text="🏆 Турниры\n\nРаздел в разработке...",
            reply_markup=get_main_menu_keyboard(
                show_admin=show_admin,
            ),
        )
    elif callback_data == "menu_ratings":
        await callback.answer("Рейтинги")
        await callback.message.edit_text(
            text="📊 Рейтинги\n\nРаздел в разработке...",
            reply_markup=get_main_menu_keyboard(
                show_admin=show_admin,
            ),
        )
    elif callback_data == "menu_bonuses":
        await callback.answer("Бонусы")
        await callback.message.edit_text(
            text="🎁 Бонусы\n\nРаздел в разработке...",
            reply_markup=get_main_menu_keyboard(
                show_admin=show_admin,
            ),
        )
    elif callback_data == "menu_wallet":
        await callback.answer("Кошелёк")
        await callback.message.edit_text(
            text="💰 Кошелёк (CD токен)\n\nРаздел в разработке...",
            reply_markup=get_main_menu_keyboard(
                show_admin=show_admin,
            ),
        )
    elif callback_data == "menu_promotions":
        await callback.answer("Акции и розыгрыши")
        await callback.message.edit_text(
            text="🎉 Акции и розыгрыши\n\nРаздел в разработке...",
            reply_markup=get_main_menu_keyboard(
                show_admin=show_admin,
            ),
        )
    elif callback_data == "menu_invite":
        await callback.answer("Пригласи друга")
        await callback.message.edit_text(
            text="🤝 Пригласи друга\n\nРаздел в разработке...",
            reply_markup=get_main_menu_keyboard(
                show_admin=show_admin,
            ),
        )
    elif callback_data == "menu_support":
        await callback.answer("Поддержка")
        await callback.message.edit_text(
            text="❓ Поддержка\n\nРаздел в разработке...",
            reply_markup=get_main_menu_keyboard(
                show_admin=show_admin,
            ),
        )
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
        _waiting_team_data[callback.from_user.id] = True
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
        await callback.message.edit_text(
            text="🏆 Турниры\n\nРаздел в разработке...",
            reply_markup=get_admin_panel_keyboard(
                is_super_admin=is_super_admin,
            ),
        )
    elif callback_data == "admin_results":
        await callback.answer("Результаты")
        await callback.message.edit_text(
            text="✅ Результаты\n\nРаздел в разработке...",
            reply_markup=get_admin_panel_keyboard(
                is_super_admin=is_super_admin,
            ),
        )
    elif callback_data == "admin_users":
        await callback.answer("Пользователи")
        await callback.message.edit_text(
            text="👥 Пользователи\n\nРаздел в разработке...",
            reply_markup=get_admin_panel_keyboard(
                is_super_admin=is_super_admin,
            ),
        )
    elif callback_data == "admin_teams":
        await callback.answer("Команды")
        await callback.message.edit_text(
            text="🧑‍🤝‍🧑 Команды\n\nРаздел в разработке...",
            reply_markup=get_admin_panel_keyboard(
                is_super_admin=is_super_admin,
            ),
        )
    elif callback_data == "admin_ratings":
        await callback.answer("Рейтинги")
        await callback.message.edit_text(
            text="📊 Рейтинги\n\nРаздел в разработке...",
            reply_markup=get_admin_panel_keyboard(
                is_super_admin=is_super_admin,
            ),
        )
    elif callback_data == "admin_wallet_bonuses":
        await callback.answer("CD токен и бонусы")
        await callback.message.edit_text(
            text="💰 CD токен и бонусы\n\nРаздел в разработке...",
            reply_markup=get_admin_panel_keyboard(
                is_super_admin=is_super_admin,
            ),
        )
    elif callback_data == "admin_promotions":
        await callback.answer("Акции и розыгрыши")
        await callback.message.edit_text(
            text="🎉 Акции и розыгрыши\n\nРаздел в разработке...",
            reply_markup=get_admin_panel_keyboard(
                is_super_admin=is_super_admin,
            ),
        )
    elif callback_data == "admin_referral":
        await callback.answer("Рефералка")
        await callback.message.edit_text(
            text="🤝 Рефералка\n\nРаздел в разработке...",
            reply_markup=get_admin_panel_keyboard(
                is_super_admin=is_super_admin,
            ),
        )
    elif callback_data == "admin_broadcast":
        await callback.answer("Рассылка")
        await callback.message.edit_text(
            text="📣 Рассылка\n\nРаздел в разработке...",
            reply_markup=get_admin_panel_keyboard(
                is_super_admin=is_super_admin,
            ),
        )
    elif callback_data == "admin_audit":
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
        await callback.message.edit_text(
            text="🧾 Журнал действий\n\nРаздел в разработке...",
            reply_markup=get_admin_panel_keyboard(
                is_super_admin=is_super_admin,
            ),
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
    user_id = message.from_user.id
    
    # Проверяем, ожидает ли пользователь ввода данных команды
    if not _waiting_team_data.get(user_id, False):
        return
    
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
