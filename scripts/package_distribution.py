"""Package the PyInstaller output into a release zip."""

from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def bundled_application(dist_dir: Path) -> Path:
    candidates = (
        dist_dir / "Plutus.app",
        dist_dir / "plutus.exe",
        dist_dir / "plutus",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise SystemExit(f"No bundled application found in {dist_dir}")


def add_to_zip(zip_file: ZipFile, path: Path, base_dir: Path) -> None:
    if path.is_file():
        zip_file.write(path, path.relative_to(base_dir))
        return

    for child in sorted(path.rglob("*")):
        if child.is_file():
            zip_file.write(child, child.relative_to(base_dir))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", required=True)
    parser.add_argument("--dist-dir", type=Path, default=Path("dist"))
    parser.add_argument("--output-dir", type=Path, default=Path("dist-artifacts"))
    args = parser.parse_args()

    app_path = bundled_application(args.dist_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / f"plutus-{args.platform}.zip"

    with ZipFile(output_path, "w", ZIP_DEFLATED) as zip_file:
        add_to_zip(zip_file, app_path, app_path.parent)

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
