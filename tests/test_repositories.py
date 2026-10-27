import tempfile
import unittest
from pathlib import Path

from src.materials_app.database import initialize_database
from src.materials_app.models import (
    Department,
    Material,
    Operation,
    OperationItem,
    Supplier,
    User,
)
from src.materials_app.repositories import (
    DepartmentRepository,
    MaterialRepository,
    OperationItemRepository,
    OperationRepository,
    SupplierRepository,
    UserRepository,
)


class RepositoryTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "repositories.db"
        initialize_database(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_material_crud(self):
        repository = MaterialRepository(self.db_path)
        material_id = repository.create(Material(None, "Щебень", "кг", 10))
        material = repository.get_by_id(material_id)
        self.assertEqual(material.name, "Щебень")
        self.assertTrue(repository.update(Material(material_id, "Щебень фракции 5", "кг", 20)))
        self.assertEqual(repository.get_by_id(material_id).min_stock, 20)
        self.assertTrue(repository.delete(material_id))
        self.assertIsNone(repository.get_by_id(material_id))

    def test_reference_entity_crud(self):
        supplier_repo = SupplierRepository(self.db_path)
        supplier_id = supplier_repo.create(Supplier(None, "ООО Тест", "+7 900 000-00-00"))
        self.assertEqual(supplier_repo.get_by_id(supplier_id).name, "ООО Тест")
        self.assertTrue(supplier_repo.update(Supplier(supplier_id, "ООО Тест 2", None)))

        department_repo = DepartmentRepository(self.db_path)
        department_id = department_repo.create(Department(None, "Тестовый участок"))
        self.assertEqual(department_repo.get_by_id(department_id).name, "Тестовый участок")
        self.assertTrue(department_repo.delete(department_id))

        user_repo = UserRepository(self.db_path)
        user_id = user_repo.create(
            User(None, "Тестовый Пользователь", "Руководитель", "test-user", "hash", True)
        )
        self.assertEqual(user_repo.get_by_login("test-user").user_id, user_id)
        self.assertTrue(user_repo.update(User(user_id, "Изменённый Пользователь", "Бухгалтер", "test-user", "hash2", False)))
        self.assertFalse(user_repo.get_by_id(user_id).operation)
        self.assertTrue(user_repo.delete(user_id))

    def test_operation_and_item_crud_with_cascade(self):
        operation_repo = OperationRepository(self.db_path)
        item_repo = OperationItemRepository(self.db_path)
        operation_id = operation_repo.create(
            Operation(None, "IN", "2026-10-20", 1, None, 1, "Тест")
        )
        item_id = item_repo.create(OperationItem(None, operation_id, 1, 5))
        self.assertEqual(operation_repo.get_by_id(operation_id).operation_type, "IN")
        self.assertEqual(item_repo.get_by_id(item_id).quantity, 5)
        self.assertTrue(item_repo.update(OperationItem(item_id, operation_id, 1, 7)))
        self.assertEqual(item_repo.get_by_id(item_id).quantity, 7)
        self.assertTrue(operation_repo.delete(operation_id))
        self.assertIsNone(item_repo.get_by_id(item_id))


if __name__ == "__main__":
    unittest.main()
