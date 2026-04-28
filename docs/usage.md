# Usage

## Running Locally

Install the project and launch the desktop application:

```bash
uv sync
uv run plutus
```

On first launch, Plutus prompts for the SQLite database file location and reuses
that saved path on later launches.

## Building A Distributable

Build the desktop binary with PyInstaller:

```bash
uv sync --extra build
uv run pyinstaller plutus.spec
```

The generated application is placed under `dist/` as `plutus` on Linux,
`plutus.exe` on Windows, or `Plutus.app` on macOS.

## Building The Documentation

Build the documentation site with MkDocs:

```bash
uv sync --extra docs
uv run mkdocs build --strict
```

The generated site is placed under `site/`.
