"""Boots a real local PostgreSQL instance with no Docker or admin rights required.

Uses `pgserver`, which bundles Postgres binaries as a pip package. Handy when
Docker Desktop isn't installed/available (e.g. no admin rights for WSL2 setup).

Usage:
    python scripts/local_postgres.py

Prints the connection URI and keeps the server running until Ctrl+C. Data
persists in backend/.devdb across restarts, so migrations only need to run
once. Point backend/.env's DATABASE_URL at the printed URI (with the
`+asyncpg` driver suffix) before running `alembic upgrade head` or `uvicorn`.
"""

import pathlib
import time

import pgserver

PGDATA = pathlib.Path(__file__).resolve().parent.parent / ".devdb"


def main() -> None:
    PGDATA.mkdir(exist_ok=True)
    db = pgserver.get_server(PGDATA, cleanup_mode=None)
    uri = db.get_uri()
    async_uri = uri.replace("postgresql://", "postgresql+asyncpg://", 1)

    print(f"Postgres running at: {uri}", flush=True)
    print("Set DATABASE_URL in backend/.env to:", flush=True)
    print(f"  DATABASE_URL={async_uri}", flush=True)
    print("Press Ctrl+C to stop.", flush=True)

    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("Stopping...")
        db.cleanup()


if __name__ == "__main__":
    main()
