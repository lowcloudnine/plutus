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

On first launch, Plutus asks where you want the SQLite file stored and
remembers that location for future launches.

## Building a distributable

Use PyInstaller with the included spec file:

```bash
uv run pyinstaller plutus.spec
```

The bundled application is written under `dist/`. Expected outputs are
`dist/plutus` on Linux, `dist/plutus.exe` on Windows, and `dist/Plutus.app` on
macOS.

## Building the documentation

Generate the HTML docs with Sphinx:

```bash
uv run sphinx-build -b html docs docs/_build/html
```
