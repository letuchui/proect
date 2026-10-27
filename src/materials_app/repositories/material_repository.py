"""Репозиторий материалов."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from ..database import DEFAULT_DB_PATH, get_connection
from ..models import Material


class MaterialRepository:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = db_path

    @staticmethod
    def _map(row: sqlite3.Row | None) -> Material | None:
        if row is None:
            return None
        return Material(row["material_id"], row["name"], row["unit"], row["min_stock"])

    def create(self, material: Material) -> int:
        with closing(get_connection(self.db_path)) as connection:
            with connection:
                cursor = connection.execute(
                    "INSERT INTO materials (name, unit, min_stock) VALUES (?, ?, ?)",
                    (material.name, material.unit, material.min_stock),
                )
                return int(cursor.lastrowid)

    def get_by_id(self, material_id: int) -> Material | None:
        with closing(get_connection(self.db_path)) as connection:
            row = connection.execute(
                "SELECT material_id, name, unit, min_stock FROM materials WHERE material_id = ?",
                (material_id,),
            ).fetchone()
        return self._map(row)

    def get_all(self) -> list[Material]:
        with closing(get_connection(self.db_path)) as connection:
            rows = connection.execute(
                "SELECT material_id, name, unit, min_stock FROM materials ORDER BY material_id"
            ).fetchall()
        return [self._map(row) for row in rows if row is not None]

    def get_all_rows(self) -> list[sqlite3.Row]:
        with closing(get_connection(self.db_path)) as connection:
            return connection.execute(
                "SELECT material_id, name, unit, min_stock FROM materials ORDER BY material_id"
            ).fetchall()

    def get_balance_rows(self) -> list[sqlite3.Row]:
        with closing(get_connection(self.db_path)) as connection:
            return connection.execute(
                """
                SELECT
                    m.material_id,
                    m.name,
                    m.unit,
                    m.min_stock,
                    COALESCE(SUM(CASE
                        WHEN o.operation_type = 'IN' THEN oi.quantity
                        WHEN o.operation_type = 'OUT' THEN -oi.quantity
                    END), 0) AS balance
                FROM materials AS m
                LEFT JOIN operation_items AS oi ON oi.material_id = m.material_id
                LEFT JOIN operations AS o ON o.operation_id = oi.operation_id
                GROUP BY m.material_id, m.name, m.unit, m.min_stock
                ORDER BY m.material_id
                """
            ).fetchall()

    def update(self, material: Material) -> bool:
        if material.material_id is None:
            raise ValueError("Для обновления нужен идентификатор материала")
        with closing(get_connection(self.db_path)) as connection:
            with connection:
                cursor = connection.execute(
                    """
                    UPDATE materials
                    SET name = ?, unit = ?, min_stock = ?
                    WHERE material_id = ?
                    """,
                    (material.name, material.unit, material.min_stock, material.material_id),
                )
                return cursor.rowcount > 0

    def delete(self, material_id: int) -> bool:
        with closing(get_connection(self.db_path)) as connection:
            with connection:
                cursor = connection.execute(
                    "DELETE FROM materials WHERE material_id = ?", (material_id,)
                )
                return cursor.rowcount > 0
