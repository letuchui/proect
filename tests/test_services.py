import tempfile
import unittest
from pathlib import Path

from src.materials_app.database import initialize_database
from src.materials_app.services import AuthService, MaterialService, MovementService
from src.materials_app.services.exceptions import (
    DuplicateEntityError,
    InsufficientStockError,
    PermissionDeniedError,
    ValidationError,
)


class ServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "services.db"
        initialize_database(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_authentication_and_registration(self):
        auth = AuthService(self.db_path)
        clerk = auth.authenticate("ivanov", "clerk123")
        self.assertIsNotNone(clerk)
        self.assertEqual(clerk.role, "Кладовщик")
        self.assertIsNone(auth.authenticate("ivanov", "wrong-password"))

        user = auth.register("Новый Пользователь", "new-login", "secret1", "Руководитель")
        self.assertEqual(user.login, "new-login")
        with self.assertRaises(DuplicateEntityError):
            auth.register("Другой Пользователь", "new-login", "secret2", "Бухгалтер")

    def test_material_validation_and_low_stock(self):
        service = MaterialService(self.db_path)
        with self.assertRaises(ValidationError):
            service.create("", "кг", 0)
        with self.assertRaises(ValidationError):
            service.create("Новый материал", "кг", -1)
        material = service.create("Новый материал", "кг", 10)
        self.assertEqual(material.name, "Новый материал")
        self.assertIn(material.material_id, {item.material_id for item in service.get_low_stock()})

    def test_movement_rules_and_balances(self):
        movements = MovementService(self.db_path)
        incoming_id = movements.add_incoming(1, 1, "2026-10-20", [(1, 10)], "Тестовый приход")
        self.assertGreater(incoming_id, 4)
        balance = {row["material_id"]: row["balance"] for row in movements.materials.get_balance_rows()}
        self.assertEqual(balance[1], 75)

        outgoing_id = movements.add_outgoing(1, 1, "2026-10-21", [(1, 5)], "Тестовый расход")
        self.assertGreater(outgoing_id, incoming_id)
        with self.assertRaises(InsufficientStockError):
            movements.add_outgoing(1, 1, "2026-10-22", [(1, 1000)])
        with self.assertRaises(PermissionDeniedError):
            movements.add_outgoing(2, 1, "2026-10-22", [(1, 1)])
        with self.assertRaises(ValidationError):
            movements.add_incoming(1, 1, "20-10-2026", [(1, 1)])


if __name__ == "__main__":
    unittest.main()
