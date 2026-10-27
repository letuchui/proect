"""Бизнес-правила прихода и расхода материалов."""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from typing import Iterable

from ..database import DEFAULT_DB_PATH
from ..models import Operation
from ..repositories.department_repository import DepartmentRepository
from ..repositories.material_repository import MaterialRepository
from ..repositories.operation_repository import OperationRepository
from ..repositories.supplier_repository import SupplierRepository
from ..repositories.user_repository import UserRepository
from .exceptions import (
    DuplicateEntityError,
    InsufficientStockError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)


class MovementService:
    WRITE_ROLES = {"Кладовщик"}

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.materials = MaterialRepository(db_path)
        self.suppliers = SupplierRepository(db_path)
        self.departments = DepartmentRepository(db_path)
        self.users = UserRepository(db_path)
        self.operations = OperationRepository(db_path)

    def _require_writer(self, user_id: int) -> None:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Пользователь не найден")
        if not user.operation or user.role not in self.WRITE_ROLES:
            raise PermissionDeniedError("У пользователя нет права изменять складские данные")

    @staticmethod
    def _validate_date(operation_date: str) -> str:
        try:
            date.fromisoformat(operation_date)
        except ValueError as error:
            raise ValidationError("Дата должна быть в формате ГГГГ-ММ-ДД") from error
        return operation_date

    def _validate_items(self, items: Iterable[tuple[int, float]]) -> list[tuple[int, float]]:
        values = list(items)
        if not values:
            raise ValidationError("Операция должна содержать хотя бы один материал")
        material_ids: set[int] = set()
        result: list[tuple[int, float]] = []
        for material_id, quantity in values:
            if material_id in material_ids:
                raise ValidationError("Один материал нельзя добавить в операцию дважды")
            if quantity <= 0:
                raise ValidationError("Количество должно быть больше нуля")
            if self.materials.get_by_id(material_id) is None:
                raise NotFoundError(f"Материал с ID {material_id} не найден")
            material_ids.add(material_id)
            result.append((material_id, float(quantity)))
        return result

    def add_incoming(
        self,
        user_id: int,
        supplier_id: int,
        operation_date: str,
        items: Iterable[tuple[int, float]],
        comment: str | None = None,
    ) -> int:
        self._require_writer(user_id)
        if self.suppliers.get_by_id(supplier_id) is None:
            raise NotFoundError("Поставщик не найден")
        values = self._validate_items(items)
        return self.operations.create_with_items(
            Operation(None, "IN", self._validate_date(operation_date), supplier_id, None, user_id, comment),
            values,
        )

    def add_outgoing(
        self,
        user_id: int,
        department_id: int,
        operation_date: str,
        items: Iterable[tuple[int, float]],
        comment: str | None = None,
    ) -> int:
        self._require_writer(user_id)
        if self.departments.get_by_id(department_id) is None:
            raise NotFoundError("Подразделение не найдено")
        values = self._validate_items(items)
        balances = {row["material_id"]: row["balance"] for row in self.materials.get_balance_rows()}
        for material_id, quantity in values:
            available = balances.get(material_id, 0)
            if quantity > available:
                raise InsufficientStockError(
                    f"Недостаточно материала с ID {material_id}: доступно {available:g}"
                )
        return self.operations.create_with_items(
            Operation(None, "OUT", self._validate_date(operation_date), None, department_id, user_id, comment),
            values,
        )

    def get_history(self):
        return self.operations.get_history_rows()
