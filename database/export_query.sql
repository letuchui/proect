-- Все операции, включая операции без позиций.
-- Двойное подчёркивание в псевдониме задаёт путь во вложенном объекте.
-- Например, items__material__name превращается в items[].material.name.
SELECT
    o.operation_id,
    o.operation_type,
    o.operation_date,
    o.comment,
    s.supplier_id AS supplier__supplier_id,
    s.name AS supplier__name,
    s.phone AS supplier__phone,
    d.department_id AS department__department_id,
    d.name AS department__name,
    u.user_id AS user__user_id,
    u.full_name AS user__full_name,
    u.role AS user__role,
    oi.item_id AS items__item_id,
    oi.quantity AS items__quantity,
    m.material_id AS items__material__material_id,
    m.name AS items__material__name,
    m.unit AS items__material__unit,
    m.min_stock AS items__material__min_stock
FROM operations AS o
LEFT JOIN suppliers AS s ON s.supplier_id = o.supplier_id
LEFT JOIN departments AS d ON d.department_id = o.department_id
LEFT JOIN users AS u ON u.user_id = o.user_id
LEFT JOIN operation_items AS oi ON oi.operation_id = o.operation_id
LEFT JOIN materials AS m ON m.material_id = oi.material_id
ORDER BY o.operation_date, o.operation_id, oi.item_id;
