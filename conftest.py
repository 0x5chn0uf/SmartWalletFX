import pathlib
import sys

# Automatically add the backend directory to Python path when pytest is run
# from the repository root. This ensures that `import app...` statements used
# across the backend tests succeed even if the current working directory is
# outside `backend/`.

ROOT_DIR = pathlib.Path(__file__).parent
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
