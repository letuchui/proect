"""Подключение к SQLite и совместимые функции инициализации проекта."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "materials.db"
SCHEMA_PATH = PROJECT_ROOT / "database" / "schema.sql"
SEED_PATH = PROJECT_ROOT / "database" / "seed.sql"


def get_connection(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Открывает SQLite-соединение с включёнными внешними ключами."""
    if str(db_path) == ":memory:":
        path = ":memory:"
    else:
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(
    db_path: str | Path = DEFAULT_DB_PATH,
    schema_path: str | Path = SCHEMA_PATH,
    seed_path: str | Path | None = SEED_PATH,
) -> None:
    """Создаёт структуру и загружает демонстрационные записи."""
    schema = Path(schema_path).read_text(encoding="utf-8")
    with closing(get_connection(db_path)) as connection:
        connection.executescript(schema)
        if seed_path is not None:
            seed = Path(seed_path).read_text(encoding="utf-8")
            connection.executescript(seed)


def _has_expected_schema(db_path: str | Path) -> bool:
    """Проверяет, что база создана актуальной схемой ЛР4."""
    try:
        with closing(get_connection(db_path)) as connection:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            required = {
                "materials",
                "suppliers",
                "departments",
                "users",
                "operations",
                "operation_items",
            }
            if not required.issubset(tables):
                return False
            user_columns = {
                row[1] for row in connection.execute("PRAGMA table_info(users)")
            }
            return {"login", "password_hash", "operation"}.issubset(user_columns)
    except sqlite3.DatabaseError:
        return False


def ensure_database(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    """Создаёт БД только при первом запуске или после устаревшей схемы."""
    if not _has_expected_schema(db_path):
        initialize_database(db_path)


# Обратная совместимость с функциями, использовавшимися в ЛР3.
def add_material(
    name: str,
    unit: str,
    min_stock: float = 0,
    *,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    from .models import Material
    from .repositories.material_repository import MaterialRepository

    return MaterialRepository(db_path).create(Material(None, name, unit, min_stock))


def add_supplier(
    name: str,
    phone: str | None = None,
    *,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    from .models import Supplier
    from .repositories.supplier_repository import SupplierRepository

    return SupplierRepository(db_path).create(Supplier(None, name, phone))


def add_department(
    name: str,
    *,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    from .models import Department
    from .repositories.department_repository import DepartmentRepository

    return DepartmentRepository(db_path).create(Department(None, name))


def add_user(
    full_name: str,
    role: str,
    *,
    login: str = "",
    password_hash: str = "",
    operation: bool = True,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    from .models import User
    from .repositories.user_repository import UserRepository

    return UserRepository(db_path).create(
        User(None, full_name, role, login, password_hash, operation)
    )


def list_materials(db_path: str | Path = DEFAULT_DB_PATH):
    from .repositories.material_repository import MaterialRepository

    return MaterialRepository(db_path).get_all_rows()


def list_balances(db_path: str | Path = DEFAULT_DB_PATH):
    from .repositories.material_repository import MaterialRepository

    return MaterialRepository(db_path).get_balance_rows()


def list_low_stock(db_path: str | Path = DEFAULT_DB_PATH):
    return [row for row in list_balances(db_path) if row["balance"] < row["min_stock"]]


def list_operations(db_path: str | Path = DEFAULT_DB_PATH):
    from .repositories.operation_repository import OperationRepository

    return OperationRepository(db_path).get_history_rows()


def add_operation(
    operation_type: str,
    operation_date: str,
    user_id: int,
    items: Iterable[tuple[int, float]],
    *,
    supplier_id: int | None = None,
    department_id: int | None = None,
    comment: str | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    from .models import Operation
    from .repositories.operation_repository import OperationRepository

    operation = Operation(
        None,
        operation_type,
        operation_date,
        supplier_id,
        department_id,
        user_id,
        comment,
    )
    return OperationRepository(db_path).create_with_items(operation, list(items))
