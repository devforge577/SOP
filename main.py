import tkinter as tk
from tkinter import messagebox
import logging
from utils.logging_config import setup_logging, log_security_event
from database.db import initialize_database
from views.login_view import LoginView
from views.cashier_view import CashierView
from views.product_view import ProductView
from views.reports_view import ReportsView
from views.user_management_view import UserManagementView
from modules.auth import Auth
from modules.products import ProductManager
from modules.sales import SalesProcessor

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class Dashboard(tk.Tk):
    """
    Main dashboard — launched after login.
    Acts as the root window and navigation hub.
    """

    def __init__(self, user: dict):
        super().__init__()
        self.user = user

        # Initialize modules with auth context
        self.auth = Auth()
        self.auth.current_user = user
        self.product_manager = ProductManager(self.auth)
        self.sales_processor = SalesProcessor(self.auth, self.product_manager)

        self.title("POS System — Dashboard")
        self.geometry("680x520")
        self.resizable(False, False)
        self.configure(bg="#1a1a2e")
        self._center_window()
        self._build_ui()

    def _center_window(self):
        self.update_idletasks()
        w, h = 680, 520
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg="#16213e", pady=20)
        header.pack(fill="x")

        tk.Label(
            header,
            text="🛒  POS System",
            font=("Segoe UI", 22, "bold"),
            bg="#16213e",
            fg="white",
        ).pack()

        tk.Label(
            header,
            text=f"Welcome, {self.user['full_name']}  ·  {self.user['role'].capitalize()}",
            font=("Segoe UI", 10),
            bg="#16213e",
            fg="#8892b0",
        ).pack(pady=(4, 0))

        # Nav buttons
        nav = tk.Frame(self, bg="#1a1a2e", pady=30)
        nav.pack(fill="both", expand=True, padx=40)

        role = self.user["role"]

        buttons = [
            (
                "🛒  Cashier / New Sale",
                "#e94560",
                self._open_cashier,
                True,
                "Available to all roles",
            ),
            (
                "📦  Product Management",
                "#0f3460",
                self._open_products,
                role in ("admin", "manager"),
                "Admin & Manager only",
            ),
            (
                "📊  Reports & Analytics",
                "#1b4332",
                self._open_reports,
                role in ("admin", "manager"),
                "Admin & Manager only",
            ),
            (
                "👥  User Management",
                "#4a235a",
                self._open_user_management,
                role == "admin",
                "Admin only",
            ),
            ("🚪  Logout", "#444", self._logout, True, ""),
        ]

        for text, color, cmd, allowed, tooltip in buttons:
            state = "normal" if allowed else "disabled"
            btn = tk.Button(
                nav,
                text=text,
                font=("Segoe UI", 12, "bold"),
                bg=color,
                fg="white",
                activebackground=color,
                activeforeground="white",
                relief="flat",
                cursor="hand2" if allowed else "arrow",
                pady=14,
                state=state,
                command=cmd,
            )
            btn.pack(fill="x", pady=5)

            # Show tooltip hint for restricted buttons
            if not allowed and tooltip:
                tk.Label(
                    nav,
                    text=f"  ↑ {tooltip}",
                    font=("Segoe UI", 7),
                    bg="#1a1a2e",
                    fg="#555",
                ).pack(anchor="w", pady=(0, 2))

        # Footer
        tk.Label(
            self,
            text="Restricted buttons require elevated role permissions.",
            font=("Segoe UI", 8),
            bg="#1a1a2e",
            fg="#444",
        ).pack(pady=(0, 10))

    def _open_cashier(self):
        CashierView(self, self.user, self.product_manager, self.sales_processor)

    def _open_products(self):
        ProductView(self, self.user, self.product_manager)

    def _open_reports(self):
        ReportsView(self, self.user, self.product_manager, self.sales_processor)

    def _open_user_management(self):
        UserManagementView(self, self.user)

    def _logout(self):
        if messagebox.askyesno("Logout", "Log out and return to the login screen?"):
            log_security_event("USER_LOGOUT", user=self.user.get("username", "unknown"))
            logger.info(f"User logged out: {self.user.get('username', 'unknown')}")
            self.auth.logout()
            self.destroy()
            app = LoginView(on_success=launch_dashboard)
            app.mainloop()


def launch_dashboard(user: dict):
    log_security_event("USER_LOGIN_SUCCESS", user=user.get("username", "unknown"))
    logger.info(
        f"User logged in: {user.get('username', 'unknown')} ({user.get('role', 'unknown')})"
    )
    dashboard = Dashboard(user)
    dashboard.mainloop()


if __name__ == "__main__":
    try:
        logger.info("Starting POS System application")
        initialize_database()
        logger.info("Database initialized successfully")
        login = LoginView(on_success=launch_dashboard)
        login.mainloop()
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        messagebox.showerror("Error", f"Failed to start application: {e}")
        raise
