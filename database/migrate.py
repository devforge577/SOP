"""
Database migration runner for POS System.
"""

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def _ensure_versions_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_versions (
            version      TEXT NOT NULL PRIMARY KEY,
            applied_at   TEXT NOT NULL DEFAULT (datetime('now')),
            description  TEXT
        )
    """
    )
    conn.commit()


def _applied_versions(conn: sqlite3.Connection) -> set:
    cursor = conn.execute("SELECT version FROM schema_versions")
    return {row[0] for row in cursor.fetchall()}


def _parse_description(filename: str) -> str:
    name = Path(filename).stem
    parts = name.split("_", 1)
    if len(parts) == 2:
        return parts[1].replace("_", " ").capitalize()
    return name


def run_migrations(conn: sqlite3.Connection) -> None:
    """Apply all pending migrations in order."""
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
        logger.debug(
            "Database schema is up to date (%d migrations applied).", len(applied)
        )
        return

    logger.info("%d pending migration(s) to apply.", len(pending))

    for migration_file in pending:
        sql = migration_file.read_text(encoding="utf-8")
        description = _parse_description(migration_file.name)
        logger.info("Applying migration: %s", migration_file.name)
        try:
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
                migration_file.name,
                e,
            )
            raise RuntimeError(
                f"Migration '{migration_file.name}' failed: {e}\n"
                "Fix the migration file and restart the application."
            ) from e


def migration_status() -> list:
    """Return the status of all migrations (applied and pending)."""
    from database.db import get_connection

    conn = get_connection()
    _ensure_versions_table(conn)
    applied = _applied_versions(conn)
    conn.close()

    migration_files = (
        sorted(MIGRATIONS_DIR.glob("*.sql")) if MIGRATIONS_DIR.exists() else []
    )
    return [
        {
            "filename": f.name,
            "description": _parse_description(f.name),
            "applied": f.name in applied,
        }
        for f in migration_files
    ]


if __name__ == "__main__":
    import sys
    from database.db import initialize_database

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
