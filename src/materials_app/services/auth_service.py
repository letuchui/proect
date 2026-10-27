"""Регистрация и авторизация пользователей."""

from __future__ import annotations

import hashlib
import secrets
import sqlite3
from pathlib import Path

from ..database import DEFAULT_DB_PATH
from ..models import User
from ..repositories.user_repository import UserRepository
from .exceptions import DuplicateEntityError, ValidationError


class AuthService:
    ROLES = ("Кладовщик", "Руководитель", "Бухгалтер")
    ITERATIONS = 120_000

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.repository = UserRepository(db_path)

    @classmethod
    def hash_password(cls, password: str, salt: bytes | None = None) -> str:
        if len(password) < 6:
            raise ValidationError("Пароль должен содержать минимум 6 символов")
        salt = salt or secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, cls.ITERATIONS
        )
        return f"{salt.hex()}${digest.hex()}"

    @classmethod
    def verify_password(cls, password: str, password_hash: str) -> bool:
        try:
            salt_hex, digest_hex = password_hash.split("$", 1)
            expected = bytes.fromhex(digest_hex)
            actual = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                bytes.fromhex(salt_hex),
                cls.ITERATIONS,
            )
        except (ValueError, TypeError):
            return False
        return secrets.compare_digest(actual, expected)

    def register(
        self,
        full_name: str,
        login: str,
        password: str,
        role: str,
        operation: bool = True,
    ) -> User:
        full_name = full_name.strip()
        login = login.strip().lower()
        if not full_name:
            raise ValidationError("ФИО не должно быть пустым")
        if not login:
            raise ValidationError("Логин не должен быть пустым")
        if role not in self.ROLES:
            raise ValidationError("Указана недопустимая роль")
        if self.repository.get_by_login(login) is not None:
            raise DuplicateEntityError("Пользователь с таким логином уже существует")

        password_hash = self.hash_password(password)
        try:
            user_id = self.repository.create(
                User(None, full_name, role, login, password_hash, operation)
            )
        except sqlite3.IntegrityError as error:
            raise DuplicateEntityError("Пользователь с таким логином уже существует") from error
        user = self.repository.get_by_id(user_id)
        assert user is not None
        return user

    def authenticate(self, login: str, password: str) -> User | None:
        user = self.repository.get_by_login(login.strip().lower())
        if user is None or not user.operation:
            return None
        return user if self.verify_password(password, user.password_hash) else None
