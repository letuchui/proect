"""Точка входа для запуска проекта из каталога src."""

try:
    from .materials_app.main import main
except ImportError:  # pragma: no cover - используется только при запуске файла напрямую
    from materials_app.main import main


if __name__ == "__main__":
    main()
