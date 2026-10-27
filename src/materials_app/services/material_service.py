"""Бизнес-операции со справочником материалов."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from ..database import DEFAULT_DB_PATH
from ..models import Material, MaterialBalance
from ..repositories.material_repository import MaterialRepository
from .exceptions import DuplicateEntityError, NotFoundError, ValidationError


class MaterialService:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.repository = MaterialRepository(db_path)

    @staticmethod
    def _text(value: str, field_name: str) -> str:
        value = value.strip()
        if not value:
            raise ValidationError(f"Поле «{field_name}» не должно быть пустым")
        return value

    def create(self, name: str, unit: str, min_stock: float = 0) -> Material:
        name = self._text(name, "название")
        unit = self._text(unit, "единица измерения")
        if min_stock < 0:
            raise ValidationError("Минимальный запас не может быть отрицательным")
        try:
            material_id = self.repository.create(Material(None, name, unit, float(min_stock)))
        except sqlite3.IntegrityError as error:
            raise DuplicateEntityError("Материал с таким названием уже существует") from error
        return self.get(material_id)

    def get(self, material_id: int) -> Material:
        material = self.repository.get_by_id(material_id)
        if material is None:
            raise NotFoundError("Материал не найден")
        return material

    def get_all(self) -> list[Material]:
        return self.repository.get_all()

    def update(self, material_id: int, name: str, unit: str, min_stock: float) -> Material:
        self.get(material_id)
        name = self._text(name, "название")
        unit = self._text(unit, "единица измерения")
        if min_stock < 0:
            raise ValidationError("Минимальный запас не может быть отрицательным")
        try:
            updated = self.repository.update(Material(material_id, name, unit, float(min_stock)))
        except sqlite3.IntegrityError as error:
            raise DuplicateEntityError("Материал с таким названием уже существует") from error
        if not updated:
            raise NotFoundError("Материал не найден")
        return self.get(material_id)

    def delete(self, material_id: int) -> None:
        self.get(material_id)
        try:
            if not self.repository.delete(material_id):
                raise NotFoundError("Материал не найден")
        except sqlite3.IntegrityError as error:
            raise ValidationError("Нельзя удалить материал, который использован в операциях") from error

    def get_balances(self) -> list[MaterialBalance]:
        return [
            MaterialBalance(
                row["material_id"],
                row["name"],
                row["unit"],
                row["min_stock"],
                row["balance"],
            )
            for row in self.repository.get_balance_rows()
        ]

    def get_low_stock(self) -> list[MaterialBalance]:
        return [row for row in self.get_balances() if row.balance < row.min_stock]
