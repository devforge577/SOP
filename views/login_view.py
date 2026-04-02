import tkinter as tk
from tkinter import messagebox, ttk
from modules.auth import login
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoginView(tk.Tk):
    """
    The main login window. On successful login it destroys itself
    and passes the logged-in user dict to the on_success callback.
    """

    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.login_attempts = 0
        self.max_attempts = 3

        self.title("POS System — Login")
        self.geometry("420x520")
        self.resizable(False, False)
        self.configure(bg="#1a1a2e")
        self._center_window()
        self._build_ui()
        
        # Set focus to username field
        self.username_entry.focus()

    def _center_window(self):
        self.update_idletasks()
        w, h = 420, 520
        x = (self.winfo_screenwidth()  // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────
        header = tk.Frame(self, bg="#16213e", pady=30)
        header.pack(fill="x")

        # Animated store icon (simple)
        self.icon_label = tk.Label(
            header, text="🛒", font=("Segoe UI Emoji", 36),
            bg="#16213e", fg="white"
        )
        self.icon_label.pack()
        
        # Animate icon on hover
        self.icon_label.bind("<Enter>", lambda e: self.icon_label.config(font=("Segoe UI Emoji", 42)))
        self.icon_label.bind("<Leave>", lambda e: self.icon_label.config(font=("Segoe UI Emoji", 36)))

        tk.Label(
            header, text="Point of Sale",
            font=("Segoe UI", 20, "bold"),
            bg="#16213e", fg="white"
        ).pack()

        tk.Label(
            header, text="Sign in to continue",
            font=("Segoe UI", 10),
            bg="#16213e", fg="#8892b0"
        ).pack(pady=(4, 0))

        # ── Form card ─────────────────────────────────────────────────────
        card = tk.Frame(self, bg="#16213e", padx=40, pady=30)
        card.pack(fill="both", expand=True, padx=30, pady=20)

        # Username
        tk.Label(
            card, text="Username",
            font=("Segoe UI", 10, "bold"),
            bg="#16213e", fg="#ccd6f6", anchor="w"
        ).pack(fill="x")

        self.username_var = tk.StringVar()
        self.username_entry = tk.Entry(
            card, textvariable=self.username_var,
            font=("Segoe UI", 12),
            bg="#0f3460", fg="white", insertbackground="white",
            relief="flat", bd=0
        )
        self.username_entry.pack(fill="x", ipady=10, pady=(4, 16))
        
        # Add placeholder effect
        self._add_placeholder(self.username_entry, "Enter username")

        # Password
        tk.Label(
            card, text="Password",
            font=("Segoe UI", 10, "bold"),
            bg="#16213e", fg="#ccd6f6", anchor="w"
        ).pack(fill="x")

        self.password_var = tk.StringVar()
        self.password_entry = tk.Entry(
            card, textvariable=self.password_var,
            font=("Segoe UI", 12), show="•",
            bg="#0f3460", fg="white", insertbackground="white",
            relief="flat", bd=0
        )
        self.password_entry.pack(fill="x", ipady=10, pady=(4, 4))
        
        # Add placeholder effect
        self._add_placeholder(self.password_entry, "Enter password", is_password=True)

        # Show/hide password toggle
        self.show_pw = tk.BooleanVar(value=False)
        self.show_pw_check = tk.Checkbutton(
            card, text="Show password",
            variable=self.show_pw, command=self._toggle_password,
            bg="#16213e", fg="#8892b0", selectcolor="#16213e",
            activebackground="#16213e", activeforeground="#8892b0",
            font=("Segoe UI", 9), cursor="hand2"
        )
        self.show_pw_check.pack(anchor="w", pady=(0, 10))

        # Error label (hidden until needed)
        self.error_var = tk.StringVar()
        self.error_label = tk.Label(
            card, textvariable=self.error_var,
            font=("Segoe UI", 9),
            bg="#16213e", fg="#ff6b6b", wraplength=300
        )
        self.error_label.pack(pady=(0, 8))

        # Login button
        self.login_btn = tk.Button(
            card, text="Sign In",
            font=("Segoe UI", 12, "bold"),
            bg="#e94560", fg="white",
            activebackground="#c73652", activeforeground="white",
            relief="flat", cursor="hand2", pady=10,
            command=self._attempt_login
        )
        self.login_btn.pack(fill="x")

        # Loading indicator (initially hidden)
        self.loading_label = tk.Label(
            card, text="Signing in...",
            font=("Segoe UI", 10),
            bg="#16213e", fg="#e94560"
        )
        
        # Remember me checkbox
        self.remember_var = tk.BooleanVar(value=False)
        remember_check = tk.Checkbutton(
            card, text="Remember me",
            variable=self.remember_var,
            bg="#16213e", fg="#8892b0", selectcolor="#16213e",
            activebackground="#16213e", activeforeground="#8892b0",
            font=("Segoe UI", 9), cursor="hand2"
        )
        remember_check.pack(anchor="w", pady=(10, 0))
        
        # Load saved credentials if any
        self._load_saved_credentials()

        # ── Footer ────────────────────────────────────────────────────────
        footer = tk.Frame(self, bg="#1a1a2e")
        footer.pack(pady=(0, 10))
        
        tk.Label(
            footer, text="Default: admin / admin123",
            font=("Segoe UI", 8),
            bg="#1a1a2e", fg="#4a4a6a"
        ).pack()
        
        tk.Label(
            footer, text="• Cashier: cashier / cashier123 • Manager: manager / manager123 •",
            font=("Segoe UI", 7),
            bg="#1a1a2e", fg="#4a4a6a"
        ).pack()

        # Version info
        tk.Label(
            footer, text="POS System v1.0",
            font=("Segoe UI", 7),
            bg="#1a1a2e", fg="#4a4a6a"
        ).pack(pady=(5, 0))

        # Bind Enter key
        self.bind("<Return>", lambda e: self._attempt_login())
        
        # Bind Escape key to close
        self.bind("<Escape>", lambda e: self._quit_app())

    def _add_placeholder(self, entry, placeholder, is_password=False):
        """Add placeholder text to entry fields"""
        original_color = entry.cget("fg")
        
        def on_focus_in(event):
            if entry.get() == placeholder:
                entry.delete(0, tk.END)
                entry.config(fg="white")
                if is_password:
                    entry.config(show="•")
        
        def on_focus_out(event):
            if not entry.get():
                entry.insert(0, placeholder)
                entry.config(fg="#8892b0")
                if is_password:
                    entry.config(show="")
        
        entry.insert(0, placeholder)
        entry.config(fg="#8892b0")
        if is_password:
            entry.config(show="")
        
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        
        # Store placeholder info for later use
        entry.placeholder = placeholder
        entry.is_placeholder_active = True

    def _toggle_password(self):
        """Toggle password visibility"""
        if self.password_entry.get() not in ["", "Enter password"]:
            self.password_entry.config(show="" if self.show_pw.get() else "•")

    def _save_credentials(self, username, password):
        """Save credentials to a file (simple implementation)"""
        if self.remember_var.get():
            try:
                import json
                import os
                
                cred_file = os.path.expanduser("~/.pos_credentials.json")
                with open(cred_file, 'w') as f:
                    json.dump({
                        'username': username,
                        'password': password,
                        'remember': True
                    }, f)
                logger.info("Credentials saved")
            except Exception as e:
                logger.error(f"Error saving credentials: {e}")
        else:
            self._clear_saved_credentials()

    def _load_saved_credentials(self):
        """Load saved credentials if they exist"""
        try:
            import json
            import os
            
            cred_file = os.path.expanduser("~/.pos_credentials.json")
            if os.path.exists(cred_file):
                with open(cred_file, 'r') as f:
                    data = json.load(f)
                    if data.get('remember'):
                        self.username_var.set(data.get('username', ''))
                        self.password_var.set(data.get('password', ''))
                        self.remember_var.set(True)
                        logger.info("Loaded saved credentials")
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")

    def _clear_saved_credentials(self):
        """Clear saved credentials"""
        try:
            import os
            cred_file = os.path.expanduser("~/.pos_credentials.json")
            if os.path.exists(cred_file):
                os.remove(cred_file)
                logger.info("Cleared saved credentials")
        except Exception as e:
            logger.error(f"Error clearing credentials: {e}")

    def _attempt_login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        # Check if placeholder values are still there
        if username == "Enter username":
            username = ""
        if password == "Enter password":
            password = ""

        if not username or not password:
            self.error_var.set("Please enter both username and password.")
            return

        # Disable button while checking
        self.login_btn.pack_forget()
        self.loading_label.pack(fill="x", pady=(10, 0))
        self.update()

        try:
            user = login(username, password)

            if user:
                # Save credentials if remember me is checked
                self._save_credentials(username, password)
                
                logger.info(f"Successful login: {username} ({user['role']})")
                self.destroy()
                self.on_success(user)
            else:
                self.login_attempts += 1
                remaining = self.max_attempts - self.login_attempts
                
                if remaining > 0:
                    self.error_var.set(f"Invalid username or password. {remaining} attempt(s) remaining.")
                    logger.warning(f"Failed login attempt {self.login_attempts}/{self.max_attempts} for {username}")
                else:
                    self.error_var.set("Maximum login attempts exceeded. Please restart the application.")
                    self.login_btn.config(state="disabled")
                    logger.error(f"Max login attempts exceeded for {username}")
                    
                    # Show dialog and quit after 3 seconds
                    messagebox.showerror(
                        "Too Many Attempts",
                        "Maximum login attempts exceeded. The application will now close."
                    )
                    self.after(3000, self._quit_app)
                
                self.password_var.set("")
                self.password_entry.focus()
        except Exception as e:
            logger.error(f"Login error: {e}")
            self.error_var.set(f"An error occurred: {str(e)}")
        finally:
            # Re-enable button (if widget still exists)
            if self.winfo_exists():
                try:
                    self.loading_label.pack_forget()
                except Exception:
                    pass
                try:
                    self.login_btn.pack(fill="x")
                except Exception:
                    pass
                self.update()

    def _quit_app(self):
        """Gracefully quit the application"""
        logger.info("Application closed by user")
        self.destroy()
        
    def on_closing(self):
        """Handle window close event"""
        if messagebox.askokcancel("Quit", "Do you want to quit the application?"):
            logger.info("Application closed by user")
            self.destroy()


# ── Quick test (run this file directly) ───────────────────────────────────
if __name__ == "__main__":
    def test_dashboard(user):
        """Test function to show successful login"""
        print(f"Logged in as: {user['full_name']} ({user['role']})")
        # Create a simple test window
        test_root = tk.Tk()
        test_root.title("Test Dashboard")
        test_root.geometry("400x300")
        test_root.configure(bg="#1a1a2e")
        
        tk.Label(
            test_root,
            text=f"Welcome, {user['full_name']}!",
            font=("Segoe UI", 16, "bold"),
            bg="#1a1a2e",
            fg="white"
        ).pack(expand=True)
        
        tk.Label(
            test_root,
            text=f"Role: {user['role'].capitalize()}",
            font=("Segoe UI", 12),
            bg="#1a1a2e",
            fg="#8892b0"
        ).pack()
        
        tk.Button(
            test_root,
            text="Close",
            command=test_root.destroy,
            bg="#e94560",
            fg="white",
            relief="flat"
        ).pack(pady=20)
        
        test_root.mainloop()
    
    # Start the login view
    app = LoginView(on_success=test_dashboard)
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()