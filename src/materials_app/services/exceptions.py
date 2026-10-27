"""Ошибки прикладного слоя."""


class AppError(Exception):
    """Базовая ошибка, которую можно показать пользователю."""


class ValidationError(AppError):
    """Входные данные не соответствуют правилам предметной области."""


class NotFoundError(AppError):
    """Требуемая запись отсутствует."""


class DuplicateEntityError(AppError):
    """Запись с такими уникальными данными уже существует."""


class PermissionDeniedError(AppError):
    """Роль или состояние пользователя не позволяют выполнить действие."""


class AuthenticationError(AppError):
    """Неверные данные входа."""


class InsufficientStockError(AppError):
    """Недостаточно материала для расходной операции."""
