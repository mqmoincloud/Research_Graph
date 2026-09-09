"""Start the backend with one command.

    uv run python run.py           migrate, seed if empty, serve
    uv run python run.py --reseed  add any missing seed accounts first

The uvicorn line stays the same as the README's: --reload-dir app matters.
Without it uvicorn watches the whole folder - including .venv and
frontend/node_modules - and Vite writing into node_modules/.vite reads as "the
code changed". POST /api/run runs the whole graph inside one request, so a
restart in the middle kills the request that is in flight.
"""

import subprocess
import sys

import uvicorn

from scripts.seed import seed

HOST = "127.0.0.1"
PORT = 8000


def migrate():
    print("==> Applying migrations")
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=True,
    )


def database_is_empty():
    from app.database import localSession
    from app.models import User

    db = localSession()
    try:
        return db.query(User).count() == 0
    finally:
        db.close()


def maybe_seed(force):
    if force:
        print("==> Seeding (--reseed)")
    elif database_is_empty():
        print("==> Empty database, seeding the starting accounts")
    else:
        print("==> Database already has users, skipping seed (use --reseed to force)")
        return

    seed()


def serve():
    print(f"==> Starting server on http://{HOST}:{PORT}  (docs at /docs)")
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True, reload_dirs=["app"])


if __name__ == "__main__":
    migrate()
    maybe_seed(force="--reseed" in sys.argv)
    serve()
