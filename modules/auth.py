from database.db import (
    get_db_connection,
    hash_password,
    verify_password,
    is_legacy_hash,
    execute_update,
)
from typing import Optional, Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


# ── Module-level functions ────────────────────────────────────────────────────


def login(username: str, password: str) -> Optional[Dict]:
    """
    Validate credentials and return the user dict on success, else None.

    Uses bcrypt.checkpw correctly — fetches the stored hash first, then
    compares.  Also migrates legacy SHA-256 hashes to bcrypt on first login.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT user_id, username, password, full_name, role, is_active
                FROM users
                WHERE username = ? AND is_active = 1
                """,
                (username.strip(),),
            )
            row = cursor.fetchone()

        if not row:
            logger.warning("Login failed — unknown user: %s", username)
            return None

        stored_hash = row["password"]

        if not verify_password(password, stored_hash):
            logger.warning("Login failed — wrong password for: %s", username)
            return None

        # Migrate legacy SHA-256 hash to bcrypt on successful login
        if is_legacy_hash(stored_hash):
            new_hash = hash_password(password)
            execute_update(
                "UPDATE users SET password = ? WHERE user_id = ?",
                (new_hash, row["user_id"]),
            )
            logger.info("Migrated legacy hash to bcrypt for user: %s", username)

        user = {
            "user_id": row["user_id"],
            "username": row["username"],
            "full_name": row["full_name"],
            "role": row["role"],
            "is_active": row["is_active"],
        }
        logger.info("Successful login: %s (%s)", username, user["role"])
        return user

    except Exception as e:
        logger.error("Login error for %s: %s", username, e)
        return None


def get_current_user(user_id: int) -> Optional[Dict]:
    """Get complete user details by ID."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT user_id, username, full_name, role, is_active, created_at
                FROM users WHERE user_id = ? AND is_active = 1
                """,
                (user_id,),
            )
            row = cursor.fetchone()
        return dict(row) if row else None
    except Exception as e:
        logger.error("Error fetching user %s: %s", user_id, e)
        return None


def get_all_users(include_inactive: bool = False) -> List[Dict]:
    """Return all users, optionally including inactive ones."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if include_inactive:
                cursor.execute(
                    "SELECT user_id, username, full_name, role, is_active, created_at FROM users ORDER BY created_at DESC"
                )
            else:
                cursor.execute(
                    "SELECT user_id, username, full_name, role, is_active, created_at"
                    " FROM users WHERE is_active = 1 ORDER BY created_at DESC"
                )
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error("Error fetching users: %s", e)
        return []


def create_user(
    username: str, password: str, full_name: str, role: str
) -> Tuple[bool, str]:
    """Create a new user. Role must be admin, manager, or cashier."""
    if role not in ("admin", "manager", "cashier"):
        return False, "Invalid role. Must be admin, manager, or cashier."
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not username or not username.strip():
        return False, "Username cannot be empty."
    if not full_name or not full_name.strip():
        return False, "Full name cannot be empty."

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password, full_name, role) VALUES (?,?,?,?)",
                (username.strip(), hash_password(password), full_name.strip(), role),
            )
        logger.info("User created: %s (%s)", username, role)
        return True, "User created successfully."
    except Exception as e:
        if "UNIQUE" in str(e):
            return False, "Username already exists."
        logger.error("Error creating user %s: %s", username, e)
        return False, f"Error creating user: {e}"


def update_user(
    user_id: int, full_name: str = None, role: str = None
) -> Tuple[bool, str]:
    """Update user information (name and/or role)."""
    updates, params = [], []
    if full_name:
        updates.append("full_name = ?")
        params.append(full_name.strip())
    if role:
        if role not in ("admin", "manager", "cashier"):
            return False, "Invalid role."
        updates.append("role = ?")
        params.append(role)
    if not updates:
        return False, "No fields to update."
    params.append(user_id)
    try:
        rows = execute_update(
            f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?",
            tuple(params),
        )
        if rows > 0:
            logger.info("User %s updated.", user_id)
            return True, "User updated successfully."
        return False, "User not found."
    except Exception as e:
        logger.error("Error updating user %s: %s", user_id, e)
        return False, f"Error updating user: {e}"


def change_password(
    user_id: int, old_password: str, new_password: str
) -> Tuple[bool, str]:
    """Allow a user to change their own password."""
    if len(new_password) < 8:
        return False, "New password must be at least 8 characters."
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if not row:
                return False, "User not found."
            if not verify_password(old_password, row["password"]):
                return False, "Current password is incorrect."
            cursor.execute(
                "UPDATE users SET password = ? WHERE user_id = ?",
                (hash_password(new_password), user_id),
            )
        logger.info("Password changed for user %s.", user_id)
        return True, "Password changed successfully."
    except Exception as e:
        logger.error("Error changing password for user %s: %s", user_id, e)
        return False, f"Error changing password: {e}"


def reset_password(user_id: int, new_password: str) -> Tuple[bool, str]:
    """Admin: reset a user's password without requiring the old one."""
    if len(new_password) < 8:
        return False, "New password must be at least 8 characters."
    try:
        rows = execute_update(
            "UPDATE users SET password = ? WHERE user_id = ?",
            (hash_password(new_password), user_id),
        )
        if rows > 0:
            logger.info("Password reset for user %s.", user_id)
            return True, "Password reset successfully."
        return False, "User not found."
    except Exception as e:
        logger.error("Error resetting password for user %s: %s", user_id, e)
        return False, f"Error resetting password: {e}"


def deactivate_user(user_id: int) -> Tuple[bool, str]:
    """Soft-delete a user account."""
    try:
        rows = execute_update(
            "UPDATE users SET is_active = 0 WHERE user_id = ?", (user_id,)
        )
        if rows > 0:
            logger.info("User %s deactivated.", user_id)
            return True, "User deactivated successfully."
        return False, "User not found."
    except Exception as e:
        logger.error("Error deactivating user %s: %s", user_id, e)
        return False, f"Error deactivating user: {e}"


def activate_user(user_id: int) -> Tuple[bool, str]:
    """Reactivate a user account."""
    try:
        rows = execute_update(
            "UPDATE users SET is_active = 1 WHERE user_id = ?", (user_id,)
        )
        if rows > 0:
            logger.info("User %s activated.", user_id)
            return True, "User activated successfully."
        return False, "User not found."
    except Exception as e:
        logger.error("Error activating user %s: %s", user_id, e)
        return False, f"Error activating user: {e}"


def delete_user(user_id: int) -> Tuple[bool, str]:
    """Permanently delete a user (blocks if the user has sales records)."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sales WHERE user_id = ?", (user_id,))
            sales_count = cursor.fetchone()[0]
            if sales_count > 0:
                return (
                    False,
                    f"Cannot delete user with {sales_count} sales records. Deactivate instead.",
                )
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        logger.info("User %s permanently deleted.", user_id)
        return True, "User permanently deleted."
    except Exception as e:
        logger.error("Error deleting user %s: %s", user_id, e)
        return False, f"Error deleting user: {e}"


def has_permission(user_role: str, required_role: str) -> bool:
    """Return True if user_role meets or exceeds required_role."""
    role_level = {"admin": 3, "manager": 2, "cashier": 1}
    return role_level.get(user_role, 0) >= role_level.get(required_role, 0)


def get_role_permissions(role: str) -> Dict[str, bool]:
    """Return the full permission map for a given role."""
    base = {
        "view_sales": True,
        "process_sale": True,
        "view_products": True,
        "manage_products": False,
        "manage_inventory": False,
        "view_reports": False,
        "manage_users": False,
        "manage_system": False,
    }
    if role == "manager":
        base.update(
            {"manage_products": True, "manage_inventory": True, "view_reports": True}
        )
    elif role == "admin":
        base.update({k: True for k in base})
    return base


# ── Auth class (session wrapper) ──────────────────────────────────────────────


class Auth:
    """Thin session wrapper around the module-level auth functions."""

    def __init__(self):
        self.current_user: Optional[Dict] = None

    def login(self, username: str, password: str) -> Tuple[bool, str]:
        user = login(username, password)
        if user:
            self.current_user = user
            return True, f"Welcome {user['full_name']}!"
        return False, "Invalid username or password."

    def logout(self) -> Tuple[bool, str]:
        self.current_user = None
        return True, "Logged out successfully."

    def has_permission(self, required_role: str) -> bool:
        if not self.current_user:
            return False
        return has_permission(self.current_user["role"], required_role)

    def get_current_user(self) -> Optional[Dict]:
        return self.current_user

    def change_password(self, old_password: str, new_password: str) -> Tuple[bool, str]:
        if not self.current_user:
            return False, "No user logged in."
        return change_password(self.current_user["user_id"], old_password, new_password)


if __name__ == "__main__":
    from database.db import initialize_database

    initialize_database()
    user = login("admin", "admin123")
    if user:
        print(f"Logged in: {user['full_name']} ({user['role']})")
        for perm, val in get_role_permissions(user["role"]).items():
            print(f"  {perm}: {val}")
    else:
        print("Login failed — check your seeded credentials in the log output.")
