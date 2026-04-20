from pathlib import Path
import sys

try:
    from .app import main
except ImportError:  # pragma: no cover - supports direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from plutus.app import main


if __name__ == "__main__":
    raise SystemExit(main())
