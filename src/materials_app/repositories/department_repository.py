"""Репозиторий подразделений."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from ..database import DEFAULT_DB_PATH, get_connection
from ..models import Department


class DepartmentRepository:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = db_path

    @staticmethod
    def _map(row: sqlite3.Row | None) -> Department | None:
        if row is None:
            return None
        return Department(row["department_id"], row["name"])

    def create(self, department: Department) -> int:
        with closing(get_connection(self.db_path)) as connection:
            with connection:
                cursor = connection.execute(
                    "INSERT INTO departments (name) VALUES (?)", (department.name,)
                )
                return int(cursor.lastrowid)

    def get_by_id(self, department_id: int) -> Department | None:
        with closing(get_connection(self.db_path)) as connection:
            row = connection.execute(
                "SELECT department_id, name FROM departments WHERE department_id = ?",
                (department_id,),
            ).fetchone()
        return self._map(row)

    def get_all(self) -> list[Department]:
        with closing(get_connection(self.db_path)) as connection:
            rows = connection.execute(
                "SELECT department_id, name FROM departments ORDER BY department_id"
            ).fetchall()
        return [self._map(row) for row in rows if row is not None]

    def update(self, department: Department) -> bool:
        if department.department_id is None:
            raise ValueError("Для обновления нужен идентификатор подразделения")
        with closing(get_connection(self.db_path)) as connection:
            with connection:
                cursor = connection.execute(
                    "UPDATE departments SET name = ? WHERE department_id = ?",
                    (department.name, department.department_id),
                )
                return cursor.rowcount > 0

    def delete(self, department_id: int) -> bool:
        with closing(get_connection(self.db_path)) as connection:
            with connection:
                cursor = connection.execute(
                    "DELETE FROM departments WHERE department_id = ?", (department_id,)
                )
                return cursor.rowcount > 0
