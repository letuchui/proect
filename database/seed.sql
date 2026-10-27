-- Демонстрационные записи для проверки базы данных.

INSERT INTO materials (name, unit, min_stock) VALUES
    ('цемент', 'кг', 50),
    ('кабель', 'м', 30),
    ('перчатки', 'шт', 100);

INSERT INTO suppliers (name, phone) VALUES
    ('ООО "стройкомп"', '+7 900 111-22-33'),
    ('ООО "стройкомп2.0"', '+7 900 444-55-66');

INSERT INTO departments (name) VALUES
    ('Ремонтный цех'),
    ('Производственный участок');

INSERT INTO users (full_name, role) VALUES
    ('Иван Иванович Иванов', 'Кладовщик'),
    ('Пупкин Василий Васильевич', 'Бухгалтер');

INSERT INTO operations
    (operation_type, operation_date, supplier_id, department_id, user_id, comment)
VALUES
    ('IN', '2026-10-01', 1, NULL, 1, 'Поставка материалов по накладной № 15'),
    ('IN', '2026-10-03', 2, NULL, 1, 'Дополнительная поставка кабеля и перчаток'),
    ('OUT', '2026-10-05', NULL, 1, 1, 'Выдача материалов ремонтному цеху'),
    ('OUT', '2026-10-06', NULL, 2, 1, 'Выдача материалов производственному участку');

INSERT INTO operation_items (operation_id, material_id, quantity) VALUES
    (1, 1, 100),
    (1, 2, 120),
    (1, 3, 300),
    (2, 2, 50),
    (2, 3, 250),
    (3, 1, 25),
    (3, 2, 40),
    (3, 3, 100),
    (4, 1, 10),
    (4, 2, 20),
    (4, 3, 50);
