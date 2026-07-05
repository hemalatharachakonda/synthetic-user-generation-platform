from pathlib import Path
import sys

_backend_dir = Path(__file__).resolve().parent.parent / "backend"
_backend_app_path = _backend_dir / "app"

if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

__path__ = [str(_backend_app_path)]
