from enum import Enum
from typing import Dict, Set


class UserRole(str, Enum):
    """
    Роли пользователей в системе.
    """
    USER = "user"  # Пользователь (юзер)
    MANAGER = "manager"  # Менеджер
    ADMIN = "admin"  # Админ
    SUPER_ADMIN = "super_admin"  # Супер-админ


# Права доступа для каждой роли
ROLE_PERMISSIONS: Dict[UserRole, Set[str]] = {
    UserRole.USER: {
        # Профиль
        "profile.create",
        "profile.edit",
        # Турниры
        "tournament.join",
        "tournament.join_team",
        # Просмотр информации
        "ratings.view",
        "wallet.view",
        "bonuses.view",
        "promotions.view",
        # Реферальная система
        "referral.invite",
    },
    UserRole.MANAGER: {
        # Все права пользователя
        "profile.create",
        "profile.edit",
        "tournament.join",
        "tournament.join_team",
        "ratings.view",
        "wallet.view",
        "bonuses.view",
        "promotions.view",
        "referral.invite",
        # Дополнительные права менеджера
        "registration.check",
        "results.confirm",
        "support.answer",
        "results.add",  # Если разрешено админом турнира
    },
    UserRole.ADMIN: {
        # Все права менеджера
        "profile.create",
        "profile.edit",
        "tournament.join",
        "tournament.join_team",
        "ratings.view",
        "wallet.view",
        "bonuses.view",
        "promotions.view",
        "referral.invite",
        "registration.check",
        "results.confirm",
        "support.answer",
        "results.add",
        # Дополнительные права админа
        "tournament.create",
        "tournament.manage",
        "team.confirm",
        "results.add",
        "results.confirm",
        "promotions.create",
        "promotions.manage",
        "wallet.manual_add",  # По разрешению
        "wallet.manual_remove",  # По разрешению
    },
    UserRole.SUPER_ADMIN: {
        # Все права админа +
        "profile.create",
        "profile.edit",
        "tournament.join",
        "tournament.join_team",
        "ratings.view",
        "wallet.view",
        "bonuses.view",
        "promotions.view",
        "referral.invite",
        "registration.check",
        "results.confirm",
        "support.answer",
        "results.add",
        "tournament.create",
        "tournament.manage",
        "team.confirm",
        "results.add",
        "results.confirm",
        "promotions.create",
        "promotions.manage",
        "wallet.manual_add",
        "wallet.manual_remove",
        # Дополнительные права супер-админа
        "role.assign",
        "referral.configure",
        "bonuses.configure",
        "currency.configure",
        "audit.view",
    },
}


def has_permission(
    role: UserRole,
    permission: str,
) -> bool:
    permissions = ROLE_PERMISSIONS.get(role, set())
    return permission in permissions


def get_role_permissions(
    role: UserRole,
) -> Set[str]:
    return ROLE_PERMISSIONS.get(role, set())


def can_assign_role(
    assigner_role: UserRole,
    target_role: UserRole,
) -> bool:
    if assigner_role != UserRole.SUPER_ADMIN:
        return False
    
    # Супер-админ может назначать только админа и менеджера
    return target_role in (UserRole.ADMIN, UserRole.MANAGER)
