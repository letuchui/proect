"""Демонстрационный запуск проекта с подключённой базой SQLite."""

from __future__ import annotations

from .database import initialize_database, list_balances, list_materials, list_operations


PROJECT_TITLE = "Учёт прихода и расхода материалов"


def main() -> str:
    """Инициализирует БД и выводит материалы, остатки и историю операций."""
    initialize_database()
    lines = [PROJECT_TITLE, "База данных SQLite успешно инициализирована.", "", "Текущие остатки:"]
    for row in list_balances():
        lines.append(f"- {row['name']}: {row['balance']:g} {row['unit']}")

    lines.extend(["", "История операций:"])
    for row in list_operations():
        operation_name = "Приход" if row["operation_type"] == "IN" else "Расход"
        lines.append(
            f"- {row['operation_date']} | {operation_name} | "
            f"{row['counterparty']} | {row['full_name']}"
        )

    message = "\n".join(lines)
    print(message)
    return message


if __name__ == "__main__":
    main()
