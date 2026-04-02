"""
Database migration runner for POS System.

How it works:
- Keeps a `schema_versions` table that records every migration that has run.
- On startup, scans the migrations/ folder for *.sql files, sorted by name.
- Runs only the ones not yet recorded in schema_versions.
- Each migration runs inside a transaction — if it fails, it rolls back and
  the app stops so you never end up with a half-applied schema.

Adding a new migration:
    1. Create migrations/NNNN_description.sql  (increment the number)
    2. Write plain SQL — use IF NOT EXISTS / IF EXISTS guards where possible.
    3. That's it. The runner picks it up automatically on next startup.
"""

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def _ensure_versions_table(conn: sqlite3.Connection) -> None:
    """Create the schema_versions tracking table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_versions (
            version      TEXT NOT NULL PRIMARY KEY,
            applied_at   TEXT NOT NULL DEFAULT (datetime('now')),
            description  TEXT
        )
    """)
    conn.commit()


def _applied_versions(conn: sqlite3.Connection) -> set:
    """Return the set of migration filenames already applied."""
    cursor = conn.execute("SELECT version FROM schema_versions")
    return {row[0] for row in cursor.fetchall()}


def _parse_description(filename: str) -> str:
    """Turn '0002_add_login_attempts.sql' into 'Add login attempts'."""
    name = Path(filename).stem          # 0002_add_login_attempts
    parts = name.split("_", 1)         # ['0002', 'add_login_attempts']
    if len(parts) == 2:
        return parts[1].replace("_", " ").capitalize()
    return name


def run_migrations(conn: sqlite3.Connection) -> None:
    """
    Apply all pending migrations in order.
    Called automatically by initialize_database().
    """
    _ensure_versions_table(conn)
    applied = _applied_versions(conn)

    if not MIGRATIONS_DIR.exists():
        logger.warning("Migrations directory not found: %s", MIGRATIONS_DIR)
        return

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    if not migration_files:
        logger.debug("No migration files found in %s", MIGRATIONS_DIR)
        return

    pending = [f for f in migration_files if f.name not in applied]

    if not pending:
        logger.debug("Database schema is up to date (%d migrations applied).", len(applied))
        return

    logger.info("%d pending migration(s) to apply.", len(pending))

    for migration_file in pending:
        sql = migration_file.read_text(encoding="utf-8")
        description = _parse_description(migration_file.name)

        logger.info("Applying migration: %s", migration_file.name)
        try:
            # Run the entire migration inside a savepoint so a failure
            # rolls back only this migration, not previous ones.
            conn.execute("BEGIN")
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO schema_versions (version, description) VALUES (?, ?)",
                (migration_file.name, description),
            )
            conn.execute("COMMIT")
            logger.info("Migration applied successfully: %s", migration_file.name)
        except Exception as e:
            conn.execute("ROLLBACK")
            logger.error(
                "Migration FAILED: %s — %s. Database has been rolled back.",
                migration_file.name, e,
            )
            raise RuntimeError(
                f"Migration '{migration_file.name}' failed: {e}\n"
                "Fix the migration file and restart the application."
            ) from e


def migration_status() -> list:
    """
    Return the status of all migrations (applied and pending).
    Useful for a future admin diagnostics screen.
    """
    from database.db import get_connection
    conn = get_connection()
    _ensure_versions_table(conn)
    applied = _applied_versions(conn)
    conn.close()

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql")) if MIGRATIONS_DIR.exists() else []
    status = []
    for f in migration_files:
        status.append({
            "filename":    f.name,
            "description": _parse_description(f.name),
            "applied":     f.name in applied,
        })
    return status


if __name__ == "__main__":
    # Run migrations manually:  python -m database.migrate
    import sys
    from database.db import get_connection, initialize_database
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

    if "--status" in sys.argv:
        print("\nMigration status:")
        for m in migration_status():
            state = "✓ applied" if m["applied"] else "✗ pending"
            print(f"  {state}  {m['filename']}  —  {m['description']}")
        print()
    else:
        initialize_database()
        print("Migrations complete.")