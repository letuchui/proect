"""Типизированные модели предметной области."""

from dataclasses import dataclass


@dataclass
class Material:
    material_id: int | None
    name: str
    unit: str
    min_stock: float = 0


@dataclass
class MaterialBalance:
    material_id: int
    name: str
    unit: str
    min_stock: float
    balance: float


@dataclass
class Supplier:
    supplier_id: int | None
    name: str
    phone: str | None = None


@dataclass
class Department:
    department_id: int | None
    name: str


@dataclass
class User:
    user_id: int | None
    full_name: str
    role: str
    login: str
    password_hash: str
    operation: bool = True


@dataclass
class Operation:
    operation_id: int | None
    operation_type: str
    operation_date: str
    supplier_id: int | None
    department_id: int | None
    user_id: int
    comment: str | None = None


@dataclass
class OperationItem:
    item_id: int | None
    operation_id: int
    material_id: int
    quantity: float


__all__ = [
    "Department",
    "Material",
    "MaterialBalance",
    "Operation",
    "OperationItem",
    "Supplier",
    "User",
]
