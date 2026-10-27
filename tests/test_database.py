import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from src.materials_app.database import (
    SCHEMA_PATH,
    add_operation,
    add_material,
    list_low_stock,
    get_connection,
    initialize_database,
    list_balances,
    list_materials,
    list_operations,
)


class DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        initialize_database(self.db_path, SCHEMA_PATH)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_all_tables_and_seed_data_exist(self):
        with closing(get_connection(self.db_path)) as connection:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
                if row[0] != "sqlite_sequence"
            }
        self.assertEqual(
            tables,
            {"materials", "suppliers", "departments", "users", "operations", "operation_items"},
        )
        self.assertGreaterEqual(len(list_materials(self.db_path)), 3)
        self.assertGreaterEqual(len(list_operations(self.db_path)), 4)

    def test_balances_are_calculated_from_operations(self):
        balances = {row["name"]: row["balance"] for row in list_balances(self.db_path)}
        self.assertEqual(balances["цемент"], 65)
        self.assertEqual(balances["кабель"], 110)
        self.assertEqual(balances["перчатки"], 400)

    def test_foreign_key_and_quantity_constraints_work(self):
        with self.assertRaises(sqlite3.IntegrityError):
            add_operation(
                "OUT",
                "2026-10-10",
                user_id=1,
                department_id=1,
                items=[(999, 1)],
                db_path=self.db_path,
            )

        with self.assertRaises(sqlite3.IntegrityError):
            add_operation(
                "IN",
                "2026-10-10",
                user_id=1,
                supplier_id=1,
                items=[(1, -1)],
                db_path=self.db_path,
            )

    def test_python_can_add_material_and_find_low_stock(self):
        material_id = add_material(
            "Краска белая",
            "л",
            min_stock=20,
            db_path=self.db_path,
        )
        self.assertGreater(material_id, 0)

        low_stock = {row["name"] for row in list_low_stock(self.db_path)}
        self.assertIn("Краска белая", low_stock)


if __name__ == "__main__":
    unittest.main()
