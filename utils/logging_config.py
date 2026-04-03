"""Logging configuration for POS system."""
import os
import logging
import logging.handlers
from pathlib import Path


def _get_logs_dir() -> Path:
    """
    Resolve the logs directory relative to this file so it works both
    when running from source and when packaged as a PyInstaller .exe.
    """
    base = Path(__file__).resolve().parent.parent
    logs_dir = base / "logs"
    logs_dir.mkdir(exist_ok=True)
    return logs_dir


def _add_handler_once(logger: logging.Logger, handler: logging.Handler) -> None:
    """Add a handler only if an identical one (same class + baseFilename) is not already attached."""
    for existing in logger.handlers:
        if type(existing) is type(handler):
            existing_file = getattr(existing, "baseFilename", None)
            new_file = getattr(handler, "baseFilename", None)
            if existing_file == new_file:
                return
    logger.addHandler(handler)


def setup_logging(log_level: int = None, log_to_file: bool = True) -> logging.Logger:
    """
    Configure structured logging for the application.

    Call this ONCE at startup (main.py already does this).
    Log level is read from the LOG_LEVEL env var; the parameter
    can override it for tests.
    """
    if log_level is None:
        level_name = os.getenv("LOG_LEVEL", "INFO").upper()
        log_level = getattr(logging, level_name, logging.INFO)

    logs_dir = _get_logs_dir()

    formatter = logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(log_level)

    # Remove any handlers added before setup_logging was called
    # (e.g. from a stray basicConfig or module-level call)
    for h in root.handlers[:]:
        root.removeHandler(h)

    # Console
    console = logging.StreamHandler()
    console.setLevel(log_level)
    console.setFormatter(formatter)
    root.addHandler(console)

    if log_to_file:
        # Daily rotating system log — one file per day, keep 30 days
        system_handler = logging.handlers.TimedRotatingFileHandler(
            logs_dir / "pos_system.log",
            when="midnight",
            backupCount=30,
            encoding="utf-8",
        )
        system_handler.setLevel(log_level)
        system_handler.setFormatter(formatter)
        root.addHandler(system_handler)

        # Errors only — size-capped so a crash loop never fills the disk
        error_handler = logging.handlers.RotatingFileHandler(
            logs_dir / "pos_errors.log",
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root.addHandler(error_handler)

    return root


def log_security_event(
    event_type: str,
    user: str = None,
    details: str = None,
    ip_address: str = None,
) -> None:
    """Log a security-related event to logs/security.log."""
    logger = logging.getLogger("security")

    if not logger.handlers:
        logs_dir = _get_logs_dir()
        handler = logging.handlers.TimedRotatingFileHandler(
            logs_dir / "security.log",
            when="midnight",
            backupCount=90,
            encoding="utf-8",
        )
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s  SECURITY  %(levelname)s  %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False  # Don't duplicate into root/system log

    parts = [f"EVENT={event_type}"]
    if user:
        parts.append(f"USER={user}")
    if ip_address:
        parts.append(f"IP={ip_address}")
    if details:
        parts.append(f"DETAILS={details}")

    logger.info("  ".join(parts))


def log_audit_event(
    action: str,
    user: str,
    resource: str = None,
    details: str = None,
) -> None:
    """Log an audit event (user actions on data) to logs/audit.log."""
    logger = logging.getLogger("audit")

    if not logger.handlers:
        logs_dir = _get_logs_dir()
        handler = logging.handlers.TimedRotatingFileHandler(
            logs_dir / "audit.log",
            when="midnight",
            backupCount=365,
            encoding="utf-8",
        )
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s  AUDIT  %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

    parts = [f"ACTION={action}", f"USER={user}"]
    if resource:
        parts.append(f"RESOURCE={resource}")
    if details:
        parts.append(f"DETAILS={details}")

    logger.info("  ".join(parts))


def log_performance(
    operation: str,
    duration_ms: float,
    details: str = None,
) -> None:
    """Log a performance metric to logs/performance.log."""
    logger = logging.getLogger("performance")

    if not logger.handlers:
        logs_dir = _get_logs_dir()
        handler = logging.handlers.RotatingFileHandler(
            logs_dir / "performance.log",
            maxBytes=20 * 1024 * 1024,  # 20 MB
            backupCount=5,
            encoding="utf-8",
        )
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s  PERF  %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

    parts = [f"OPERATION={operation}", f"DURATION_MS={duration_ms:.1f}"]
    if details:
        parts.append(f"DETAILS={details}")

    logger.info("  ".join(parts))
