"""Database backup and restore utilities."""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
import logging
from utils.logging_config import log_security_event

logger = logging.getLogger(__name__)

# Create backups directory
BACKUP_DIR = Path("backups")
BACKUP_DIR.mkdir(exist_ok=True)


def create_backup(backup_name=None, include_logs=True):
    """
    Create a backup of the database and optionally logs.

    Args:
        backup_name: Custom name for backup, auto-generated if None
        include_logs: Whether to include log files in backup

    Returns:
        Path to created backup file
    """
    try:
        # Generate backup name if not provided
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"pos_backup_{timestamp}"

        backup_path = BACKUP_DIR / f"{backup_name}.db"

        # Copy database file
        db_path = Path("database/pos_system.db")
        if db_path.exists():
            shutil.copy2(db_path, backup_path)
            logger.info(f"Database backup created: {backup_path}")
        else:
            raise FileNotFoundError("Database file not found")

        # Create full backup archive if including logs
        if include_logs:
            archive_name = f"{backup_name}_full"
            archive_path = BACKUP_DIR / archive_name

            # Create archive with database and logs
            shutil.make_archive(str(archive_path), "zip", ".", "database")
            if Path("logs").exists():
                shutil.make_archive(str(archive_path), "zip", ".", "logs")

            logger.info(f"Full backup archive created: {archive_path}.zip")
            return archive_path.with_suffix(".zip")

        log_security_event("BACKUP_CREATED", details=f"Backup: {backup_name}")
        return backup_path

    except Exception as e:
        logger.error(f"Backup creation failed: {e}")
        raise


def list_backups():
    """List all available backups."""
    backups = []
    for file_path in BACKUP_DIR.iterdir():
        if file_path.suffix in [".db", ".zip"]:
            stat = file_path.stat()
            backups.append(
                {
                    "name": file_path.stem,
                    "path": str(file_path),
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "type": "database" if file_path.suffix == ".db" else "archive",
                }
            )

    return sorted(backups, key=lambda x: x["created"], reverse=True)


def restore_backup(backup_path, confirm=True):
    """
    Restore database from backup.

    Args:
        backup_path: Path to backup file
        confirm: Whether to ask for confirmation (for interactive use)
    """
    backup_path = Path(backup_path)

    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    if confirm:
        response = input(
            f"Restore from {backup_path}? This will overwrite current database. (y/N): "
        )
        if response.lower() != "y":
            print("Restore cancelled.")
            return

    try:
        # Create backup of current state before restore
        current_backup = create_backup("pre_restore_backup", include_logs=False)

        # Restore database
        db_path = Path("database/pos_system.db")
        if backup_path.suffix == ".zip":
            # Extract from archive
            temp_dir = BACKUP_DIR / "temp_restore"
            shutil.unpack_archive(backup_path, temp_dir)
            extracted_db = temp_dir / "database" / "pos_system.db"
            if extracted_db.exists():
                shutil.copy2(extracted_db, db_path)
            shutil.rmtree(temp_dir)
        else:
            # Direct database file
            shutil.copy2(backup_path, db_path)

        logger.info(f"Database restored from: {backup_path}")
        log_security_event("BACKUP_RESTORED", details=f"From: {backup_path}")

        # Verify restore
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        conn.close()

        logger.info(f"Restore verification: {user_count} users found")
        return True

    except Exception as e:
        logger.error(f"Restore failed: {e}")
        # Attempt to restore from pre-restore backup
        try:
            restore_backup(current_backup, confirm=False)
            logger.info("Rolled back to pre-restore state")
        except Exception:
            logger.error("Rollback failed")
        raise


def cleanup_old_backups(keep_days=30, keep_count=10):
    """
    Clean up old backup files.

    Args:
        keep_days: Keep backups newer than this many days
        keep_count: Minimum number of recent backups to keep
    """
    try:
        now = datetime.now()
        backups = list_backups()

        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x["created"], reverse=True)

        to_delete = []

        # Keep minimum count
        for i, backup in enumerate(backups):
            if i < keep_count:
                continue

            # Check age
            created = datetime.fromisoformat(backup["created"])
            age_days = (now - created).days

            if age_days > keep_days:
                to_delete.append(backup)

        # Delete old backups
        for backup in to_delete:
            path = Path(backup["path"])
            path.unlink()
            logger.info(f"Deleted old backup: {path}")

        log_security_event(
            "BACKUP_CLEANUP", details=f"Deleted {len(to_delete)} old backups"
        )

    except Exception as e:
        logger.error(f"Backup cleanup failed: {e}")


def automated_backup_schedule():
    """Setup automated backup schedule (would be called by scheduler)."""
    try:
        # Daily backup
        create_backup("daily_backup", include_logs=True)

        # Cleanup old backups
        cleanup_old_backups()

        logger.info("Automated backup completed")

    except Exception as e:
        logger.error(f"Automated backup failed: {e}")


if __name__ == "__main__":
    # CLI interface for manual backup operations
    import sys

    if len(sys.argv) < 2:
        print("Usage: python backup.py <command> [args]")
        print("Commands:")
        print("  create [name]          - Create backup")
        print("  list                   - List backups")
        print("  restore <path>         - Restore from backup")
        print("  cleanup                - Clean old backups")
        sys.exit(1)

    command = sys.argv[1]

    if command == "create":
        name = sys.argv[2] if len(sys.argv) > 2 else None
        path = create_backup(name)
        print(f"Backup created: {path}")

    elif command == "list":
        backups = list_backups()
        if not backups:
            print("No backups found")
        else:
            print("Available backups:")
            for backup in backups:
                print(
                    f"  {backup['name']} ({backup['type']}) - {backup['created']} - {backup['size']} bytes"
                )

    elif command == "restore":
        if len(sys.argv) < 3:
            print("Error: backup path required")
            sys.exit(1)
        restore_backup(sys.argv[2])

    elif command == "cleanup":
        cleanup_old_backups()
        print("Cleanup completed")

    else:
        print(f"Unknown command: {command}")
