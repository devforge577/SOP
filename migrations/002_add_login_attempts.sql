-- Migration 0002: Add login_attempts table
-- Tracks failed login attempts per username for rate limiting.

CREATE TABLE IF NOT EXISTS login_attempts (
    attempt_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    username     TEXT    NOT NULL,
    attempted_at TEXT    NOT NULL DEFAULT (datetime('now')),
    success      INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_login_attempts_username ON login_attempts(username);
CREATE INDEX IF NOT EXISTS idx_login_attempts_time     ON login_attempts(attempted_at);