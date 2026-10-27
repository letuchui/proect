PRAGMA foreign_keys = OFF;

DROP TABLE IF EXISTS operation_items;
DROP TABLE IF EXISTS operations;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS departments;
DROP TABLE IF EXISTS suppliers;
DROP TABLE IF EXISTS materials;

PRAGMA foreign_keys = ON;

CREATE TABLE materials (
    material_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    unit TEXT NOT NULL,
    min_stock REAL NOT NULL DEFAULT 0 CHECK (min_stock >= 0)
);

CREATE TABLE suppliers (
    supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    phone TEXT
);

CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('Кладовщик', 'Руководитель', 'Бухгалтер')),
    login TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    operation INTEGER NOT NULL DEFAULT 1 CHECK (operation IN (0, 1))
);

CREATE TABLE operations (
    operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_type TEXT NOT NULL CHECK (operation_type IN ('IN', 'OUT')),
    operation_date TEXT NOT NULL,
    supplier_id INTEGER,
    department_id INTEGER,
    user_id INTEGER NOT NULL,
    comment TEXT,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    FOREIGN KEY (department_id) REFERENCES departments(department_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    CHECK (
        (operation_type = 'IN' AND supplier_id IS NOT NULL AND department_id IS NULL)
        OR
        (operation_type = 'OUT' AND supplier_id IS NULL AND department_id IS NOT NULL)
    )
);

CREATE TABLE operation_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_id INTEGER NOT NULL,
    material_id INTEGER NOT NULL,
    quantity REAL NOT NULL CHECK (quantity > 0),
    FOREIGN KEY (operation_id) REFERENCES operations(operation_id) ON DELETE CASCADE,
    FOREIGN KEY (material_id) REFERENCES materials(material_id),
    UNIQUE (operation_id, material_id)
);
