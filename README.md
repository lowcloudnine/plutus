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
- Generate documentation with MkDocs Material.

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

## Downloads

Prebuilt Linux, Windows, and macOS distributions are published on the latest
GitHub Release:

https://github.com/lowcloudnine/plutus/releases/latest

Direct downloads:

- Linux: https://github.com/lowcloudnine/plutus/releases/latest/download/plutus-linux.zip
- Windows: https://github.com/lowcloudnine/plutus/releases/latest/download/plutus-windows.zip
- macOS: https://github.com/lowcloudnine/plutus/releases/latest/download/plutus-macos.zip

## Building the documentation

Generate the HTML docs with MkDocs:

```bash
uv sync --extra docs
uv run mkdocs build --strict
```
