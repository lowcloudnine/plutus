# Python Environment and Dependency Management

All Python work follows a deterministic setup to minimize environment drift and dependency conflicts.

### Tooling

Use `uv` for all environment and dependency operations. Do not use `pip`, `poetry`, or `conda` directly.

### Python Version

Default to **Python 3.14** for all new projects and environments unless explicitly specified otherwise.

### Project Root (Default)

- Default project root is the current working directory (`cwd`).
- Monorepo rule: if the task clearly targets a subdirectory that contains dependency files, treat that subdirectory as the project root for env setup. Otherwise use the repo root.

### Dependency Declaration (Explicit)

A project is considered to declare dependencies if **any** of these exist at the project root:

- `pyproject.toml`
- `requirements.txt`
- `requirements-dev.txt`
- `requirements.lock`

Other files (e.g., `requirements.in`, `Pipfile`, `setup.cfg`) are ignored unless the user explicitly asks to use them.

### Environment Selection Rules (Defaults)

1. Prefer a project-local virtual environment in `<project-root>/.venv`.
2. Create one only if the project declares dependencies.
3. If `.venv` already exists in the project root, reuse it.
4. If no dependency files exist, use the shared global environment.

### Decision Tree (Default Flow)

1. Does `<project-root>/pyproject.toml` exist?

- Yes ->
  - `uv venv .venv --python 3.14`
  - `uv sync`
  - `source .venv/bin/activate`
  - If no lockfile exists, allow `uv sync` to create it.

2. Else, does `<project-root>/requirements.txt` exist?

- Yes ->
  - `uv venv .venv --python 3.14`
  - `uv pip install -r requirements.txt`
  - If running tests/linters and `requirements-dev.txt` exists, also:
    - `uv pip install -r requirements-dev.txt`
  - `source .venv/bin/activate`

3. Else, does `<project-root>/requirements-dev.txt` exist (and no `requirements.txt`)?

- Yes ->
  - `uv venv .venv --python 3.14`
  - `uv pip install -r requirements-dev.txt`
  - `source .venv/bin/activate`

4. Else ->

- `dev`
- Use `uv pip` only if new deps are strictly required.

### Activation Requirement

Always activate the environment **before**:

- Running scripts
- Installing dependencies
- Executing tests
- Invoking Python CLIs

Activation command:

bash
source .venv/bin/activate

Note: `uv sync` and `uv run` can operate without manual activation, but explicit activation is required for direct script execution.

### Global Environment Fallback

If **no dependency files exist**, use the shared global environment:

bash
source ~/personal/bin/activate

When operating in the global environment:

- Use `uv pip` exclusively.
- Never use `pip` directly.
- Avoid adding new dependencies unless strictly required.

### Non-Negotiables

- Do not mix environments within a session.
- Do not install dependencies implicitly.
- Do not assume system Python.
- Do not create ad-hoc virtual environments outside the project directory.
- Always use Python 3.14 for new projects unless explicitly specified otherwise.
- Use `uv sync` for projects with `pyproject.toml` and dependency declarations.
