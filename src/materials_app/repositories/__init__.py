"""Репозитории доступа к отдельным сущностям базы данных."""

from .department_repository import DepartmentRepository
from .material_repository import MaterialRepository
from .operation_item_repository import OperationItemRepository
from .operation_repository import OperationRepository
from .supplier_repository import SupplierRepository
from .user_repository import UserRepository

__all__ = [
    "DepartmentRepository",
    "MaterialRepository",
    "OperationItemRepository",
    "OperationRepository",
    "SupplierRepository",
    "UserRepository",
]
