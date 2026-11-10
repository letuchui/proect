"""ЛР5: экспорт связанных данных SQLite в JSON, CSV, XML и YAML.

Запуск из корня проекта: python -m src.materials_app.exporter
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from xml.etree import ElementTree as ET

from .database import DEFAULT_DB_PATH, PROJECT_ROOT, initialize_database
from .repositories.operation_repository import OperationRepository


DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "out"
Record = dict[str, Any]


def load_operations(db_path: str | Path = DEFAULT_DB_PATH) -> tuple[list[Record], list[str]]:
    """Извлекает актуальные данные SQL-запросом, не пересоздавая существующую БД."""
    if not Path(db_path).is_file():
        raise FileNotFoundError(f"База данных не найдена: {db_path}")
    return OperationRepository(db_path).get_export_rows()


def _nest_fields(fields: Mapping[str, Any]) -> Record:
    """Разворачивает псевдонимы вида user__name в вложенные словари."""
    result: Record = {}
    for name, value in fields.items():
        parts = name.split("__")
        target = result
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value
    return result


def _collapse_null_objects(value: Any) -> Any:
    """Отсутствующая связь LEFT JOIN представляется одним значением null."""
    if isinstance(value, dict):
        nested = {key: _collapse_null_objects(item) for key, item in value.items()}
        return None if all(item is None for item in nested.values()) else nested
    return value


def build_nested_data(
    rows: Iterable[Mapping[str, Any]],
    *,
    id_field: str = "operation_id",
    collection_field: str = "items",
    collection_id: str = "item_id",
) -> list[Record]:
    """Группирует строки JOIN: один объект на запись и список связанных позиций.

    Поля определяются по псевдонимам SQL, а не по фиксированному перечню.
    Для другой основной таблицы можно изменить имена ключей в аргументах.
    """
    grouped: dict[Any, Record] = {}
    seen_items: dict[Any, set[Any]] = {}
    prefix = collection_field + "__"
    for row in rows:
        record_id = row[id_field]
        if record_id not in grouped:
            grouped[record_id] = _nest_fields(
                {key: value for key, value in row.items() if not key.startswith(prefix)}
            )
            grouped[record_id] = _collapse_null_objects(grouped[record_id])
            grouped[record_id][collection_field] = []
            seen_items[record_id] = set()
        item_id = row.get(prefix + collection_id)
        if item_id is not None and item_id not in seen_items[record_id]:
            item = _nest_fields(
                {key[len(prefix):]: value for key, value in row.items() if key.startswith(prefix)}
            )
            grouped[record_id][collection_field].append(_collapse_null_objects(item))
            seen_items[record_id].add(item_id)
    return list(grouped.values())


def export_json(data: list[Record], path: str | Path) -> None:
    with Path(path).open("w", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def export_csv(rows: Sequence[Mapping[str, Any]], columns: Sequence[str], path: str | Path) -> None:
    """Одна строка на позицию; имена колонок отражают путь во вложенном объекте."""
    with Path(path).open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=[name.replace("__", ".") for name in columns])
        writer.writeheader()
        for row in rows:
            writer.writerow({key.replace("__", "."): value for key, value in row.items()})


def _fill_xml(element: ET.Element, value: Any) -> None:
    """Рекурсивно записывает словари, списки и скаляры, сохраняя тип в атрибуте."""
    if value is None:
        element.set("type", "null")
    elif isinstance(value, dict):
        element.set("type", "object")
        for key, item in value.items():
            _fill_xml(ET.SubElement(element, key), item)
    elif isinstance(value, list):
        element.set("type", "array")
        for item in value:
            _fill_xml(ET.SubElement(element, "item"), item)
    elif isinstance(value, bool):
        element.set("type", "boolean")
        element.text = "true" if value else "false"
    elif isinstance(value, int):
        element.set("type", "integer")
        element.text = str(value)
    elif isinstance(value, float):
        element.set("type", "number")
        element.text = str(value)
    else:
        element.set("type", "string")
        element.text = str(value)


def export_xml(data: list[Record], path: str | Path) -> None:
    root = ET.Element("data")
    _fill_xml(root, data)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def _yaml_module():
    try:
        import yaml
    except ModuleNotFoundError as error:
        raise RuntimeError("Установите PyYAML: python -m pip install PyYAML") from error
    return yaml


def export_yaml(data: list[Record], path: str | Path) -> None:
    yaml = _yaml_module()
    with Path(path).open("w", encoding="utf-8") as stream:
        yaml.safe_dump(data, stream, allow_unicode=True, sort_keys=False)


def export_all(
    db_path: str | Path = DEFAULT_DB_PATH,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Path]:
    """Получает один снимок данных и формирует четыре файла в указанной папке."""
    _yaml_module()
    rows, columns = load_operations(db_path)
    data = build_nested_data(rows)
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    paths = {extension: directory / f"data.{extension}" for extension in ("json", "csv", "xml", "yaml")}
    export_json(data, paths["json"])
    export_csv(rows, columns, paths["csv"])
    export_xml(data, paths["xml"])
    export_yaml(data, paths["yaml"])
    return paths


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Экспорт операций в JSON, CSV, XML и YAML")
    parser.add_argument("--db", type=Path, help="Путь к SQLite-базе (по умолчанию data/materials.db)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT_DIR, help="Папка результата")
    args = parser.parse_args(argv)
    try:
        _yaml_module()
        # Только при обычном первом запуске создаём стандартную демонстрационную БД.
        # Ошибка в пути --db не должна незаметно создать новую базу вместо нужной.
        db_path = args.db if args.db is not None else DEFAULT_DB_PATH
        if args.db is None and not db_path.exists():
            initialize_database(db_path)
        paths = export_all(db_path, args.out)
    except (OSError, sqlite3.Error, RuntimeError) as error:
        parser.exit(1, f"Ошибка экспорта: {error}\n")
    print("Экспорт завершён. Созданы файлы:")
    for path in paths.values():
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
