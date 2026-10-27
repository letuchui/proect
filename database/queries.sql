-- Примеры запросов для демонстрации работы базы данных.

-- Остатки материалов.
SELECT
    m.name,
    m.unit,
    COALESCE(SUM(CASE
        WHEN o.operation_type = 'IN' THEN oi.quantity
        WHEN o.operation_type = 'OUT' THEN -oi.quantity
    END), 0) AS balance,
    m.min_stock
FROM materials AS m
LEFT JOIN operation_items AS oi ON oi.material_id = m.material_id
LEFT JOIN operations AS o ON o.operation_id = oi.operation_id
GROUP BY m.material_id, m.name, m.unit, m.min_stock
ORDER BY m.name;

-- Материалы, запас которых ниже минимального.
SELECT *
FROM (
    SELECT
        m.name,
        m.unit,
        COALESCE(SUM(CASE
            WHEN o.operation_type = 'IN' THEN oi.quantity
            WHEN o.operation_type = 'OUT' THEN -oi.quantity
        END), 0) AS balance,
        m.min_stock
    FROM materials AS m
    LEFT JOIN operation_items AS oi ON oi.material_id = m.material_id
    LEFT JOIN operations AS o ON o.operation_id = oi.operation_id
    GROUP BY m.material_id, m.name, m.unit, m.min_stock
)
WHERE balance < min_stock;

-- История движения материалов.
SELECT
    o.operation_date,
    CASE o.operation_type WHEN 'IN' THEN 'Приход' ELSE 'Расход' END AS operation_name,
    m.name AS material,
    oi.quantity,
    COALESCE(s.name, d.name) AS counterparty,
    u.full_name AS responsible_user
FROM operations AS o
JOIN operation_items AS oi ON oi.operation_id = o.operation_id
JOIN materials AS m ON m.material_id = oi.material_id
LEFT JOIN suppliers AS s ON s.supplier_id = o.supplier_id
LEFT JOIN departments AS d ON d.department_id = o.department_id
JOIN users AS u ON u.user_id = o.user_id
ORDER BY o.operation_date, o.operation_id, m.name;
