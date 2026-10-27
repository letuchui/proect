"""Консольный пользовательский интерфейс приложения."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Callable

from .database import DEFAULT_DB_PATH, ensure_database
from .services import AuthService, MaterialService, MovementService
from .services.exceptions import AppError


PROJECT_TITLE = "Учёт прихода и расхода материалов"
InputFn = Callable[[str], str]
OutputFn = Callable[[str], None]


class ConsoleApp:
    """CLI, который взаимодействует с приложением только через сервисы."""

    def __init__(
        self,
        db_path: str | Path = DEFAULT_DB_PATH,
        input_fn: InputFn = input,
        output_fn: OutputFn = print,
    ):
        self.input = input_fn
        self.output = output_fn
        self.auth = AuthService(db_path)
        self.materials = MaterialService(db_path)
        self.movements = MovementService(db_path)
        self._messages: list[str] = []

    def say(self, message: str = "") -> None:
        self._messages.append(message)
        self.output(message)

    def run(self) -> str:
        self.say(PROJECT_TITLE)
        self.say("Консольная система учёта материалов")
        try:
            while True:
                self.say("\n1. Войти\n2. Зарегистрироваться\n0. Выход")
                choice = self.input("Выберите действие: ").strip()
                if choice == "1":
                    self._login()
                elif choice == "2":
                    self._register()
                elif choice == "0":
                    self.say("Работа завершена.")
                    break
                else:
                    self.say("Неизвестная команда.")
        except (EOFError, KeyboardInterrupt):
            self.say("\nРабота завершена.")
        return "\n".join(self._messages)

    def _login(self) -> None:
        login = self.input("Логин: ").strip()
        password = self.input("Пароль: ")
        user = self.auth.authenticate(login, password)
        if user is None:
            self.say("Неверный логин, пароль или пользователь отключён.")
            return
        self.say(f"Вход выполнен: {user.full_name} ({user.role}).")
        self._user_menu(user.user_id, user.role, user.full_name)

    def _register(self) -> None:
        try:
            full_name = self.input("ФИО: ")
            login = self.input("Новый логин: ")
            password = self.input("Пароль (не менее 6 символов): ")
            role = self._choose_role()
            user = self.auth.register(full_name, login, password, role)
            self.say(f"Пользователь {user.login} зарегистрирован.")
        except (AppError, ValueError) as error:
            self.say(f"Ошибка регистрации: {error}")

    def _choose_role(self) -> str:
        self.say("Роли: 1 — Кладовщик, 2 — Руководитель, 3 — Бухгалтер")
        role_choice = self.input("Выберите роль: ").strip()
        roles = {"1": "Кладовщик", "2": "Руководитель", "3": "Бухгалтер"}
        if role_choice not in roles:
            raise ValueError("Неизвестная роль")
        return roles[role_choice]

    def _user_menu(self, user_id: int | None, role: str, full_name: str) -> None:
        if user_id is None:
            return
        while True:
            if role == "Кладовщик":
                self.say(
                    f"\n===== Кладовщик: {full_name} =====\n"
                    "1. Материалы\n2. Остатки\n3. Оформить приход\n"
                    "4. Оформить расход\n5. История операций\n"
                    "6. Добавить материал\n0. Выйти из аккаунта"
                )
            else:
                self.say(
                    f"\n===== {role}: {full_name} =====\n"
                    "1. Остатки\n2. История операций\n3. Материалы ниже минимума\n"
                    "0. Выйти из аккаунта"
                )
            choice = self.input("Выберите действие: ").strip()
            try:
                if choice == "0":
                    self.say("Выход из аккаунта выполнен.")
                    return
                if choice == "1" and role == "Кладовщик":
                    self._show_materials()
                elif choice == "1":
                    self._show_balances()
                elif choice == "2" and role == "Кладовщик":
                    self._show_balances()
                elif choice == "2":
                    self._show_history()
                elif choice == "3" and role == "Кладовщик":
                    self._add_incoming(user_id)
                elif choice == "3":
                    self._show_low_stock()
                elif choice == "4" and role == "Кладовщик":
                    self._add_outgoing(user_id)
                elif choice == "5" and role == "Кладовщик":
                    self._show_history()
                elif choice == "6" and role == "Кладовщик":
                    self._add_material()
                else:
                    self.say("Неизвестная команда для этой роли.")
            except (AppError, ValueError) as error:
                self.say(f"Ошибка: {error}")

    def _show_materials(self) -> None:
        self.say("Материалы:")
        for material in self.materials.get_all():
            self.say(f"{material.material_id}. {material.name} ({material.unit})")

    def _show_balances(self) -> None:
        self.say("Остатки:")
        for balance in self.materials.get_balances():
            marker = " [ниже минимума]" if balance.balance < balance.min_stock else ""
            self.say(
                f"{balance.material_id}. {balance.name}: "
                f"{balance.balance:g} {balance.unit}{marker}"
            )

    def _show_low_stock(self) -> None:
        low_stock = self.materials.get_low_stock()
        if not low_stock:
            self.say("Материалов ниже минимального запаса нет.")
            return
        self.say("Материалы ниже минимального запаса:")
        for balance in low_stock:
            self.say(f"{balance.name}: {balance.balance:g} из {balance.min_stock:g} {balance.unit}")

    def _show_history(self) -> None:
        self.say("История операций:")
        for row in self.movements.get_history():
            operation_name = "Приход" if row["operation_type"] == "IN" else "Расход"
            self.say(
                f"{row['operation_date']} | {operation_name} | "
                f"{row['counterparty']} | {row['full_name']}"
            )

    def _add_material(self) -> None:
        name = self.input("Название материала: ")
        unit = self.input("Единица измерения: ")
        min_stock = float(self.input("Минимальный запас: "))
        material = self.materials.create(name, unit, min_stock)
        self.say(f"Материал создан с ID {material.material_id}.")

    def _choose_material_and_quantity(self) -> tuple[int, float]:
        self._show_materials()
        material_id = int(self.input("ID материала: "))
        quantity = float(self.input("Количество: "))
        return material_id, quantity

    def _add_incoming(self, user_id: int) -> None:
        suppliers = self.movements.suppliers.get_all()
        self.say("Поставщики:")
        for supplier in suppliers:
            self.say(f"{supplier.supplier_id}. {supplier.name}")
        supplier_id = int(self.input("ID поставщика: "))
        material_id, quantity = self._choose_material_and_quantity()
        operation_date = self.input(f"Дата [{date.today().isoformat()}]: ").strip() or date.today().isoformat()
        comment = self.input("Комментарий: ").strip() or None
        operation_id = self.movements.add_incoming(
            user_id, supplier_id, operation_date, [(material_id, quantity)], comment
        )
        self.say(f"Приход оформлен, номер операции: {operation_id}.")

    def _add_outgoing(self, user_id: int) -> None:
        departments = self.movements.departments.get_all()
        self.say("Подразделения:")
        for department in departments:
            self.say(f"{department.department_id}. {department.name}")
        department_id = int(self.input("ID подразделения: "))
        material_id, quantity = self._choose_material_and_quantity()
        operation_date = self.input(f"Дата [{date.today().isoformat()}]: ").strip() or date.today().isoformat()
        comment = self.input("Комментарий: ").strip() or None
        operation_id = self.movements.add_outgoing(
            user_id, department_id, operation_date, [(material_id, quantity)], comment
        )
        self.say(f"Расход оформлен, номер операции: {operation_id}.")


def summary(db_path: str | Path = DEFAULT_DB_PATH) -> str:
    """Формирует краткий отчёт без запуска интерактивного меню."""
    ensure_database(db_path)
    material_service = MaterialService(db_path)
    movement_service = MovementService(db_path)
    lines = [PROJECT_TITLE, "База данных SQLite готова.", "", "Текущие остатки:"]
    for balance in material_service.get_balances():
        lines.append(f"- {balance.name}: {balance.balance:g} {balance.unit}")
    lines.append("")
    lines.append("История операций:")
    for row in movement_service.get_history():
        operation_name = "Приход" if row["operation_type"] == "IN" else "Расход"
        lines.append(
            f"- {row['operation_date']} | {operation_name} | "
            f"{row['counterparty']} | {row['full_name']}"
        )
    return "\n".join(lines)


def main(
    *,
    db_path: str | Path = DEFAULT_DB_PATH,
    interactive: bool = True,
    input_fn: InputFn = input,
    output_fn: OutputFn = print,
) -> str:
    ensure_database(db_path)
    if not interactive:
        message = summary(db_path)
        output_fn(message)
        return message
    return ConsoleApp(db_path, input_fn, output_fn).run()


if __name__ == "__main__":
    main()
