"""Репозиторий операций движения материалов."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Iterable

from ..database import DEFAULT_DB_PATH, get_connection
from ..models import Operation


class OperationRepository:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = db_path

    @staticmethod
    def _map(row: sqlite3.Row | None) -> Operation | None:
        if row is None:
            return None
        return Operation(
            row["operation_id"],
            row["operation_type"],
            row["operation_date"],
            row["supplier_id"],
            row["department_id"],
            row["user_id"],
            row["comment"],
        )

    def create(self, operation: Operation) -> int:
        with closing(get_connection(self.db_path)) as connection:
            with connection:
                cursor = connection.execute(
                    """
                    INSERT INTO operations
                        (operation_type, operation_date, supplier_id, department_id, user_id, comment)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        operation.operation_type,
                        operation.operation_date,
                        operation.supplier_id,
                        operation.department_id,
                        operation.user_id,
                        operation.comment,
                    ),
                )
                return int(cursor.lastrowid)

    def create_with_items(
        self,
        operation: Operation,
        items: Iterable[tuple[int, float]],
    ) -> int:
        item_values = list(items)
        if not item_values:
            raise ValueError("Операция должна содержать хотя бы один материал")

        with closing(get_connection(self.db_path)) as connection:
            with connection:
                cursor = connection.execute(
                    """
                    INSERT INTO operations
                        (operation_type, operation_date, supplier_id, department_id, user_id, comment)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        operation.operation_type,
                        operation.operation_date,
                        operation.supplier_id,
                        operation.department_id,
                        operation.user_id,
                        operation.comment,
                    ),
                )
                operation_id = int(cursor.lastrowid)
                connection.executemany(
                    """
                    INSERT INTO operation_items (operation_id, material_id, quantity)
                    VALUES (?, ?, ?)
                    """,
                    [(operation_id, material_id, quantity) for material_id, quantity in item_values],
                )
                return operation_id

    def get_by_id(self, operation_id: int) -> Operation | None:
        with closing(get_connection(self.db_path)) as connection:
            row = connection.execute(
                """
                SELECT operation_id, operation_type, operation_date,
                       supplier_id, department_id, user_id, comment
                FROM operations WHERE operation_id = ?
                """,
                (operation_id,),
            ).fetchone()
        return self._map(row)

    def get_all(self) -> list[Operation]:
        with closing(get_connection(self.db_path)) as connection:
            rows = connection.execute(
                """
                SELECT operation_id, operation_type, operation_date,
                       supplier_id, department_id, user_id, comment
                FROM operations ORDER BY operation_date, operation_id
                """
            ).fetchall()
        return [self._map(row) for row in rows if row is not None]

    def get_history_rows(self) -> list[sqlite3.Row]:
        with closing(get_connection(self.db_path)) as connection:
            return connection.execute(
                """
                SELECT
                    o.operation_id,
                    o.operation_type,
                    o.operation_date,
                    COALESCE(s.name, d.name) AS counterparty,
                    u.full_name,
                    o.comment
                FROM operations AS o
                LEFT JOIN suppliers AS s ON s.supplier_id = o.supplier_id
                LEFT JOIN departments AS d ON d.department_id = o.department_id
                JOIN users AS u ON u.user_id = o.user_id
                ORDER BY o.operation_date, o.operation_id
                """
            ).fetchall()

    def update(self, operation: Operation) -> bool:
        if operation.operation_id is None:
            raise ValueError("Для обновления нужен идентификатор операции")
        with closing(get_connection(self.db_path)) as connection:
            with connection:
                cursor = connection.execute(
                    """
                    UPDATE operations
                    SET operation_type = ?, operation_date = ?, supplier_id = ?,
                        department_id = ?, user_id = ?, comment = ?
                    WHERE operation_id = ?
                    """,
                    (
                        operation.operation_type,
                        operation.operation_date,
                        operation.supplier_id,
                        operation.department_id,
                        operation.user_id,
                        operation.comment,
                        operation.operation_id,
                    ),
                )
                return cursor.rowcount > 0

    def delete(self, operation_id: int) -> bool:
        with closing(get_connection(self.db_path)) as connection:
            with connection:
                cursor = connection.execute(
                    "DELETE FROM operations WHERE operation_id = ?", (operation_id,)
                )
                return cursor.rowcount > 0
