"""Запуск экспорта из PyCharm или командой python src/export_data.py."""

if __package__:
    from .materials_app.exporter import main
else:
    from materials_app.exporter import main


if __name__ == "__main__":
    raise SystemExit(main())
