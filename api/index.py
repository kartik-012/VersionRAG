import os
import sys

# Ensure backend directory is in Python search path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(root_dir, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Override storage and database directory for serverless environments (read-only filesystem except /tmp)
if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    os.environ.setdefault("STORAGE_LOCAL_DIR", "/tmp/versionrag_storage")
    os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/versionrag.db")

from app.main import app  # noqa: E402
