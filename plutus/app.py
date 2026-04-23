"""Compatibility wrapper for the Plutus desktop application entrypoint."""

from __future__ import annotations

from .ui.main_window import MainWindow, build_application, default_database_path, main

__all__ = ["MainWindow", "build_application", "default_database_path", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
