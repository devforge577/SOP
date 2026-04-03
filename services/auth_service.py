"""
Authentication Service

Handles user authentication and session management.
"""

from typing import Optional, Dict, Tuple
from modules.auth import login as auth_login, Auth
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Service layer for authentication operations."""

    def __init__(self):
        self.current_session = None
        self.auth = Auth()

    def authenticate(
        self, username: str, password: str
    ) -> Tuple[bool, Optional[Dict], str]:
        try:
            user = auth_login(username, password)
            if user:
                self.current_session = user
                self.auth.current_user = user
                logger.info("Session started for %s", username)
                return True, user, f"Welcome {user['full_name']}!"
            else:
                logger.warning("Authentication failed for %s", username)
                return False, None, "Invalid username or password"
        except Exception as e:
            logger.error("Authentication error: %s", e)
            return False, None, f"Authentication error: {str(e)}"

    def get_current_user(self) -> Optional[Dict]:
        return self.current_session

    def is_authenticated(self) -> bool:
        return self.current_session is not None

    def logout(self) -> Tuple[bool, str]:
        if self.current_session:
            username = self.current_session.get("username", "User")
            self.current_session = None
            self.auth.current_user = None
            logger.info("Session ended for %s", username)
            return True, "Logged out successfully"
        return False, "No active session"

    def has_role(self, required_role: str) -> bool:
        if not self.current_session:
            return False
        user_role = self.current_session.get("role", "cashier")
        role_hierarchy = {"admin": 3, "manager": 2, "cashier": 1}
        return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0)

    def user_has_permission(self, permission: str) -> bool:
        if not self.current_session:
            return False
        role = self.current_session.get("role", "cashier")
        permissions = {
            "admin": [
                "view_sales",
                "process_sale",
                "view_products",
                "manage_products",
                "manage_inventory",
                "view_reports",
                "manage_users",
                "manage_system",
            ],
            "manager": [
                "view_sales",
                "process_sale",
                "view_products",
                "manage_products",
                "manage_inventory",
                "view_reports",
            ],
            "cashier": ["view_sales", "process_sale", "view_products"],
        }
        return permission in permissions.get(role, [])
