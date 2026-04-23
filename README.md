# metal_tracker

# :coin: A place for tracking, recording and calculating a stack.

# Plutus

Plutus is a simple PyQt6 desktop CRUD application for tracking gold and silver
holdings in a local SQLite database.

## Features

- Add, edit, delete, and view gold and silver holdings.
- Store data locally in SQLite.
- Show running totals for ounces and total cost by metal.
- Bundle the desktop app with PyInstaller.
- Generate documentation with Sphinx using the Furo theme.

## Running the application

Use `uv` to create the environment, install dependencies, and launch the app:

```bash
uv sync
uv run plutus
```

The SQLite database is stored at `~/.local/share/plutus/plutus.sqlite3`.

## Building a distributable

Use PyInstaller with the included spec file:

```bash
uv run pyinstaller plutus.spec
```

The bundled application will be written to `dist/plutus/`.

## Building the documentation

Generate the HTML docs with Sphinx:

```bash
uv run sphinx-build -b html docs docs/_build/html
```
