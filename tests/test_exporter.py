import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

import yaml

from src.materials_app.database import PROJECT_ROOT, get_connection, initialize_database
from src.materials_app.exporter import build_nested_data, export_all, main


def read_xml(element):
    """Читает типизированный XML для проверки обратного преобразования."""
    value_type = element.get("type")
    if value_type == "array":
        return [read_xml(child) for child in element]
    if value_type == "object":
        return {child.tag: read_xml(child) for child in element}
    if value_type == "null":
        return None
    if value_type == "integer":
        return int(element.text)
    if value_type == "number":
        return float(element.text)
    if value_type == "boolean":
        return element.text == "true"
    return element.text or ""


class ExporterTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.db_path = self.root / "materials.db"
        self.output_dir = self.root / "nested" / "out"
        initialize_database(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_export_contains_all_operations_and_related_items_in_four_formats(self):
        before = hashlib.sha256(self.db_path.read_bytes()).digest()
        paths = export_all(self.db_path, self.output_dir)
        self.assertEqual({path.name for path in paths.values()}, {
            "data.json", "data.csv", "data.xml", "data.yaml",
        })
        data = json.loads(paths["json"].read_text(encoding="utf-8"))
        self.assertEqual(len(data), 4)
        self.assertEqual(sum(len(operation["items"]) for operation in data), 11)
        self.assertEqual(data[0]["supplier"]["name"], 'ООО "стройкомп"')
        self.assertIsNone(data[0]["department"])
        self.assertEqual(data[0]["user"]["full_name"], "Иван Иванович Иванов")
        self.assertEqual(data[0]["items"][0]["material"]["name"], "цемент")
        self.assertEqual(data[0]["items"][0]["quantity"], 100)
        self.assertIsInstance(data[0]["items"][0]["quantity"], (int, float))
        self.assertIsNone(data[2]["supplier"])
        self.assertEqual(data[2]["department"]["name"], "Ремонтный цех")
        self.assertEqual(yaml.safe_load(paths["yaml"].read_text(encoding="utf-8")), data)
        self.assertEqual(read_xml(ET.parse(paths["xml"]).getroot()), data)
        with paths["csv"].open(encoding="utf-8-sig", newline="") as stream:
            flat_rows = list(csv.DictReader(stream))
        self.assertEqual(len(flat_rows), 11)
        self.assertEqual(flat_rows[0]["items.material.name"], "цемент")
        self.assertEqual(float(flat_rows[0]["items.quantity"]), 100)
        self.assertEqual(flat_rows[0]["supplier.name"], 'ООО "стройкомп"')
        self.assertEqual(flat_rows[0]["department.name"], "")
        self.assertEqual(sum(float(row["items.quantity"]) for row in flat_rows
                             if row["items.material.name"] == "цемент"), 135)
        self.assertEqual(hashlib.sha256(self.db_path.read_bytes()).digest(), before)
        for path in paths.values():
            self.assertNotIn("password_hash", path.read_text(encoding="utf-8-sig"))

    def test_repeated_export_reads_updated_data_and_escapes_special_characters(self):
        export_all(self.db_path, self.output_dir)
        unusual_name = 'Кабель, "силовой"; <новый> & запас\nвторая строка'
        with closing(get_connection(self.db_path)) as connection:
            with connection:
                connection.execute("UPDATE materials SET name = ? WHERE material_id = 2", (unusual_name,))
                connection.execute("UPDATE operations SET comment = '' WHERE operation_id = 1")
        paths = export_all(self.db_path, self.output_dir)
        data = json.loads(paths["json"].read_text(encoding="utf-8"))
        self.assertEqual(data[0]["items"][1]["material"]["name"], unusual_name)
        self.assertEqual(data[0]["comment"], "")
        self.assertEqual(yaml.safe_load(paths["yaml"].read_text(encoding="utf-8")), data)
        self.assertEqual(read_xml(ET.parse(paths["xml"]).getroot()), data)
        with paths["csv"].open(encoding="utf-8-sig", newline="") as stream:
            flat_rows = list(csv.DictReader(stream))
        self.assertEqual(flat_rows[1]["items.material.name"], unusual_name)

    def test_empty_database_produces_readable_files_and_csv_headers(self):
        initialize_database(self.db_path, seed_path=None)
        paths = export_all(self.db_path, self.output_dir)
        self.assertEqual(json.loads(paths["json"].read_text(encoding="utf-8")), [])
        self.assertEqual(yaml.safe_load(paths["yaml"].read_text(encoding="utf-8")), [])
        self.assertEqual(read_xml(ET.parse(paths["xml"]).getroot()), [])
        with paths["csv"].open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            self.assertIn("operation_id", reader.fieldnames)
            self.assertIn("items.material.name", reader.fieldnames)
            self.assertEqual(list(reader), [])

    def test_operation_without_items_is_preserved(self):
        with closing(get_connection(self.db_path)) as connection:
            with connection:
                cursor = connection.execute(
                    "INSERT INTO operations (operation_type, operation_date, supplier_id, user_id) "
                    "VALUES ('IN', '2026-11-10', 1, 1)"
                )
                operation_id = cursor.lastrowid
        paths = export_all(self.db_path, self.output_dir)
        data = json.loads(paths["json"].read_text(encoding="utf-8"))
        self.assertEqual(len(data), 5)
        self.assertEqual(data[-1]["operation_id"], operation_id)
        self.assertEqual(data[-1]["items"], [])
        with paths["csv"].open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 12)
        self.assertEqual(rows[-1]["items.item_id"], "")

    def test_grouping_supports_other_entities_and_additional_fields(self):
        row = {
            "order_id": 42, "customer__name": "Покупатель",
            "lines__line_id": 9, "lines__product__name": "Цемент",
            "lines__product__new_field": "Новое поле", "lines__quantity": 1.5,
        }
        data = build_nested_data(
            [row, row], id_field="order_id", collection_field="lines", collection_id="line_id"
        )
        self.assertEqual(len(data), 1)
        self.assertEqual(len(data[0]["lines"]), 1)
        self.assertEqual(data[0]["customer"]["name"], "Покупатель")
        self.assertEqual(data[0]["lines"][0]["product"]["new_field"], "Новое поле")

    def test_script_runs_from_another_directory(self):
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "src" / "export_data.py"),
             "--db", str(self.db_path), "--out", str(self.output_dir)],
            cwd=self.root, capture_output=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(list(self.output_dir.iterdir())), 4)

    def test_missing_database_is_not_replaced_with_demo_data(self):
        missing = self.root / "missing.db"
        with self.assertRaises(FileNotFoundError):
            export_all(missing, self.output_dir)
        self.assertFalse(missing.exists())
        self.assertFalse(self.output_dir.exists())
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "src" / "export_data.py"),
             "--db", str(missing), "--out", str(self.output_dir)],
            cwd=self.root, capture_output=True, timeout=30,
        )
        self.assertEqual(result.returncode, 1)
        self.assertFalse(missing.exists())

    def test_first_launch_creates_default_database_and_next_launch_keeps_changes(self):
        first_db = self.root / "first_launch" / "materials.db"
        with patch("src.materials_app.exporter.DEFAULT_DB_PATH", first_db), \
             patch("src.materials_app.exporter.DEFAULT_OUTPUT_DIR", self.output_dir), \
             redirect_stdout(StringIO()):
            self.assertEqual(main([]), 0)
            self.assertTrue(first_db.exists())
            with closing(get_connection(first_db)) as connection:
                with connection:
                    connection.execute("UPDATE materials SET name = 'Цемент М500' WHERE material_id = 1")
            self.assertEqual(main([]), 0)
        data = json.loads((self.output_dir / "data.json").read_text(encoding="utf-8"))
        self.assertEqual(data[0]["items"][0]["material"]["name"], "Цемент М500")


if __name__ == "__main__":
    unittest.main()
