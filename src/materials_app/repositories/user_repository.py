"""Репозиторий пользователей."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from ..database import DEFAULT_DB_PATH, get_connection
from ..models import User


class UserRepository:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = db_path

    @staticmethod
    def _map(row: sqlite3.Row | None) -> User | None:
        if row is None:
            return None
        return User(
            row["user_id"],
            row["full_name"],
            row["role"],
            row["login"],
            row["password_hash"],
            bool(row["operation"]),
        )

    def create(self, user: User) -> int:
        with closing(get_connection(self.db_path)) as connection:
            with connection:
                cursor = connection.execute(
                    """
                    INSERT INTO users (full_name, role, login, password_hash, operation)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user.full_name, user.role, user.login, user.password_hash, int(user.operation)),
                )
                return int(cursor.lastrowid)

    def get_by_id(self, user_id: int) -> User | None:
        with closing(get_connection(self.db_path)) as connection:
            row = connection.execute(
                """
                SELECT user_id, full_name, role, login, password_hash, operation
                FROM users WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()
        return self._map(row)

    def get_by_login(self, login: str) -> User | None:
        with closing(get_connection(self.db_path)) as connection:
            row = connection.execute(
                """
                SELECT user_id, full_name, role, login, password_hash, operation
                FROM users WHERE login = ?
                """,
                (login,),
            ).fetchone()
        return self._map(row)

    def get_all(self) -> list[User]:
        with closing(get_connection(self.db_path)) as connection:
            rows = connection.execute(
                """
                SELECT user_id, full_name, role, login, password_hash, operation
                FROM users ORDER BY user_id
                """
            ).fetchall()
        return [self._map(row) for row in rows if row is not None]

    def update(self, user: User) -> bool:
        if user.user_id is None:
            raise ValueError("Для обновления нужен идентификатор пользователя")
        with closing(get_connection(self.db_path)) as connection:
            with connection:
                cursor = connection.execute(
                    """
                    UPDATE users
                    SET full_name = ?, role = ?, login = ?, password_hash = ?, operation = ?
                    WHERE user_id = ?
                    """,
                    (
                        user.full_name,
                        user.role,
                        user.login,
                        user.password_hash,
                        int(user.operation),
                        user.user_id,
                    ),
                )
                return cursor.rowcount > 0

    def delete(self, user_id: int) -> bool:
        with closing(get_connection(self.db_path)) as connection:
            with connection:
                cursor = connection.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
                return cursor.rowcount > 0
