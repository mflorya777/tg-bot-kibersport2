from typing import Optional
from aiogram import types
from aiogram.filters import Command

from src.modules.keyboards import (
    get_main_menu_keyboard,
    get_admin_panel_keyboard,
)
from src.models.user_roles import UserRole


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
    # TODO: Реализовать получение пользователя из базы данных
    # Когда будет подключена база данных, нужно будет:
    # from src.clients.mongo.mongo_client import MongoClient
    # from src.config import MongoConfig
    # mongo_config = MongoConfig()
    # mongo_client = MongoClient(mongo_config)
    # user = await mongo_client.get_user(user_id)
    # return user.role if user else UserRole.USER
    
    # ВРЕМЕННО: Для тестирования админ-панели возвращаем роль админа
    # После подключения базы данных заменить на код выше
    return UserRole.ADMIN


def has_admin_access(
    role: UserRole,
) -> bool:
    """
    Проверяет, есть ли у пользователя доступ к админ-панели.
    Доступ имеют: менеджер, админ, супер-админ.
    
    Args:
        role: Роль пользователя
    
    Returns:
        True, если есть доступ, иначе False
    """
    return role in (
        UserRole.MANAGER,
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    )


async def start_handler(
    message: types.Message,
) -> None:
    user_role = await get_user_role(
        message.from_user.id,
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
        await callback.message.edit_text(
            text="🧑 Профиль\n\nРаздел в разработке...",
            reply_markup=get_main_menu_keyboard(
                show_admin=show_admin,
            ),
        )
    elif callback_data == "menu_team":
        await callback.answer("Команда")
        await callback.message.edit_text(
            text="👥 Команда\n\nРаздел в разработке...",
            reply_markup=get_main_menu_keyboard(
                show_admin=show_admin,
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
        if not has_admin_access(user_role):
            await callback.answer(
                "У вас нет доступа к админ-панели",
                show_alert=True,
            )
            return
        
        await callback.answer("Админ-панель")
        is_super_admin = user_role == UserRole.SUPER_ADMIN
        await callback.message.edit_text(
            text="⚙️ Админ-панель",
            reply_markup=get_admin_panel_keyboard(
                is_super_admin=is_super_admin,
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
    """
    callback_data = callback.data
    user_role = await get_user_role(
        callback.from_user.id,
    )
    is_super_admin = user_role == UserRole.SUPER_ADMIN
    
    # Проверка доступа
    if not has_admin_access(user_role):
        await callback.answer(
            "У вас нет доступа к админ-панели",
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
        if not is_super_admin:
            await callback.answer(
                "Доступно только супер-админам",
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
        if not is_super_admin:
            await callback.answer(
                "Доступно только супер-админам",
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
