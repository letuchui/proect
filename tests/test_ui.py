import tempfile
import unittest
from pathlib import Path

from src.materials_app.database import initialize_database
from src.materials_app.main import ConsoleApp


class ConsoleTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "ui.db"
        initialize_database(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_clerk_can_login_and_logout(self):
        commands = iter(["1", "ivanov", "clerk123", "0", "0"])
        output: list[str] = []
        app = ConsoleApp(self.db_path, lambda _: next(commands), output.append)
        result = app.run()
        self.assertIn("Вход выполнен", result)
        self.assertTrue(any("Кладовщик" in line for line in output))

    def test_registration_is_available_from_main_menu(self):
        commands = iter(["2", "Тестовый Регистратор", "registered", "secret1", "2", "0"])
        output: list[str] = []
        app = ConsoleApp(self.db_path, lambda _: next(commands), output.append)
        result = app.run()
        self.assertIn("зарегистрирован", result)


if __name__ == "__main__":
    unittest.main()
