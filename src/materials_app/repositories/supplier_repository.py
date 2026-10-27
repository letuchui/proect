"""Репозиторий поставщиков."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from ..database import DEFAULT_DB_PATH, get_connection
from ..models import Supplier


class SupplierRepository:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = db_path

    @staticmethod
    def _map(row: sqlite3.Row | None) -> Supplier | None:
        if row is None:
            return None
        return Supplier(row["supplier_id"], row["name"], row["phone"])

    def create(self, supplier: Supplier) -> int:
        with closing(get_connection(self.db_path)) as connection:
            with connection:
                cursor = connection.execute(
                    "INSERT INTO suppliers (name, phone) VALUES (?, ?)",
                    (supplier.name, supplier.phone),
                )
                return int(cursor.lastrowid)

    def get_by_id(self, supplier_id: int) -> Supplier | None:
        with closing(get_connection(self.db_path)) as connection:
            row = connection.execute(
                "SELECT supplier_id, name, phone FROM suppliers WHERE supplier_id = ?",
                (supplier_id,),
            ).fetchone()
        return self._map(row)

    def get_all(self) -> list[Supplier]:
        with closing(get_connection(self.db_path)) as connection:
            rows = connection.execute(
                "SELECT supplier_id, name, phone FROM suppliers ORDER BY supplier_id"
            ).fetchall()
        return [self._map(row) for row in rows if row is not None]

    def update(self, supplier: Supplier) -> bool:
        if supplier.supplier_id is None:
            raise ValueError("Для обновления нужен идентификатор поставщика")
        with closing(get_connection(self.db_path)) as connection:
            with connection:
                cursor = connection.execute(
                    "UPDATE suppliers SET name = ?, phone = ? WHERE supplier_id = ?",
                    (supplier.name, supplier.phone, supplier.supplier_id),
                )
                return cursor.rowcount > 0

    def delete(self, supplier_id: int) -> bool:
        with closing(get_connection(self.db_path)) as connection:
            with connection:
                cursor = connection.execute(
                    "DELETE FROM suppliers WHERE supplier_id = ?", (supplier_id,)
                )
                return cursor.rowcount > 0
