"""Слой доступа к SQLite-базе проекта учёта материалов."""

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
    """Открывает соединение и включает контроль внешних ключей."""
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
    """Пересоздаёт структуру и загружает тестовые данные из seed.sql."""
    schema = Path(schema_path).read_text(encoding="utf-8")
    with closing(get_connection(db_path)) as connection:
        connection.executescript(schema)
        if seed_path is not None:
            seed = Path(seed_path).read_text(encoding="utf-8")
            connection.executescript(seed)


def add_material(
    name: str,
    unit: str,
    min_stock: float = 0,
    *,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    """Добавляет материал в справочник и возвращает его идентификатор."""
    with closing(get_connection(db_path)) as connection:
        with connection:
            cursor = connection.execute(
                "INSERT INTO materials (name, unit, min_stock) VALUES (?, ?, ?)",
                (name, unit, min_stock),
            )
            return int(cursor.lastrowid)


def add_supplier(
    name: str,
    phone: str | None = None,
    *,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    """Добавляет поставщика и возвращает его идентификатор."""
    with closing(get_connection(db_path)) as connection:
        with connection:
            cursor = connection.execute(
                "INSERT INTO suppliers (name, phone) VALUES (?, ?)",
                (name, phone),
            )
            return int(cursor.lastrowid)


def add_department(
    name: str,
    *,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    """Добавляет подразделение-получателя."""
    with closing(get_connection(db_path)) as connection:
        with connection:
            cursor = connection.execute(
                "INSERT INTO departments (name) VALUES (?)",
                (name,),
            )
            return int(cursor.lastrowid)


def add_user(
    full_name: str,
    role: str,
    *,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    """Добавляет пользователя с ролью, заданной ограничениями БД."""
    with closing(get_connection(db_path)) as connection:
        with connection:
            cursor = connection.execute(
                "INSERT INTO users (full_name, role) VALUES (?, ?)",
                (full_name, role),
            )
            return int(cursor.lastrowid)


def list_materials(db_path: str | Path = DEFAULT_DB_PATH) -> list[sqlite3.Row]:
    """Возвращает справочник материалов."""
    with closing(get_connection(db_path)) as connection:
        return connection.execute(
            """
            SELECT material_id, name, unit, min_stock
            FROM materials
            ORDER BY material_id
            """
        ).fetchall()


def list_balances(db_path: str | Path = DEFAULT_DB_PATH) -> list[sqlite3.Row]:
    """Рассчитывает остатки как приход минус расход."""
    with closing(get_connection(db_path)) as connection:
        return connection.execute(
            """
            SELECT
                m.material_id,
                m.name,
                m.unit,
                m.min_stock,
                COALESCE(SUM(
                    CASE
                        WHEN o.operation_type = 'IN' THEN oi.quantity
                        WHEN o.operation_type = 'OUT' THEN -oi.quantity
                    END
                ), 0) AS balance
            FROM materials AS m
            LEFT JOIN operation_items AS oi ON oi.material_id = m.material_id
            LEFT JOIN operations AS o ON o.operation_id = oi.operation_id
            GROUP BY m.material_id, m.name, m.unit, m.min_stock
            ORDER BY m.material_id
            """
        ).fetchall()


def list_low_stock(db_path: str | Path = DEFAULT_DB_PATH) -> list[sqlite3.Row]:
    """Возвращает материалы, остаток которых ниже минимального запаса."""
    return [row for row in list_balances(db_path) if row["balance"] < row["min_stock"]]


def list_operations(db_path: str | Path = DEFAULT_DB_PATH) -> list[sqlite3.Row]:
    """Возвращает историю операций с ответственным лицом."""
    with closing(get_connection(db_path)) as connection:
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
    """Добавляет операцию и её строки в одной транзакции."""
    item_values = list(items)
    if not item_values:
        raise ValueError("Операция должна содержать хотя бы один материал")

    with closing(get_connection(db_path)) as connection:
        with connection:
            cursor = connection.execute(
                """
                INSERT INTO operations
                    (operation_type, operation_date, supplier_id, department_id, user_id, comment)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (operation_type, operation_date, supplier_id, department_id, user_id, comment),
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
