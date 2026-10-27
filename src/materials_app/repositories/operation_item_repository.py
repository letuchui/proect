"""Репозиторий позиций операций."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from ..database import DEFAULT_DB_PATH, get_connection
from ..models import OperationItem


class OperationItemRepository:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = db_path

    @staticmethod
    def _map(row: sqlite3.Row | None) -> OperationItem | None:
        if row is None:
            return None
        return OperationItem(row["item_id"], row["operation_id"], row["material_id"], row["quantity"])

    def create(self, item: OperationItem) -> int:
        with closing(get_connection(self.db_path)) as connection:
            with connection:
                cursor = connection.execute(
                    """
                    INSERT INTO operation_items (operation_id, material_id, quantity)
                    VALUES (?, ?, ?)
                    """,
                    (item.operation_id, item.material_id, item.quantity),
                )
                return int(cursor.lastrowid)

    def get_by_id(self, item_id: int) -> OperationItem | None:
        with closing(get_connection(self.db_path)) as connection:
            row = connection.execute(
                """
                SELECT item_id, operation_id, material_id, quantity
                FROM operation_items WHERE item_id = ?
                """,
                (item_id,),
            ).fetchone()
        return self._map(row)

    def get_all(self) -> list[OperationItem]:
        with closing(get_connection(self.db_path)) as connection:
            rows = connection.execute(
                """
                SELECT item_id, operation_id, material_id, quantity
                FROM operation_items ORDER BY item_id
                """
            ).fetchall()
        return [self._map(row) for row in rows if row is not None]

    def update(self, item: OperationItem) -> bool:
        if item.item_id is None:
            raise ValueError("Для обновления нужна идентификатор позиции")
        with closing(get_connection(self.db_path)) as connection:
            with connection:
                cursor = connection.execute(
                    """
                    UPDATE operation_items
                    SET operation_id = ?, material_id = ?, quantity = ?
                    WHERE item_id = ?
                    """,
                    (item.operation_id, item.material_id, item.quantity, item.item_id),
                )
                return cursor.rowcount > 0

    def delete(self, item_id: int) -> bool:
        with closing(get_connection(self.db_path)) as connection:
            with connection:
                cursor = connection.execute(
                    "DELETE FROM operation_items WHERE item_id = ?", (item_id,)
                )
                return cursor.rowcount > 0
