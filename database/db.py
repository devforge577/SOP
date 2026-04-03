import sqlite3
import bcrypt
import hashlib
import os
import secrets
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Database path ─────────────────────────────────────────────────────────────
_raw_url = os.getenv("DATABASE_URL", "")
if not _raw_url:
    raise EnvironmentError(
        "DATABASE_URL is not set. Add it to your .env file.\n"
        "Example: DATABASE_URL=sqlite:///pos_system.db"
    )
DB_PATH = _raw_url.replace("sqlite:///", "").replace("sqlite://", "")

# ── Secret key enforcement ────────────────────────────────────────────────────
_secret_key = os.getenv("SECRET_KEY", "")
if not _secret_key or _secret_key == "dev-key-change-in-production":
    raise EnvironmentError(
        "SECRET_KEY is not set or is using the default placeholder.\n"
        "Generate a secure key and add it to your .env file:\n"
        '  python -c "import secrets; print(secrets.token_hex(32))"'
    )


def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Automatically handles commit/rollback and connection closing.
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verify a password against a stored hash.

    Supports both bcrypt hashes (production) and legacy SHA-256 hashes.
    On a successful SHA-256 match the caller should re-hash and store the
    bcrypt version so old hashes are migrated out over time.
    """
    try:
        # bcrypt hashes always start with $2b$ or $2a$
        if stored_hash.startswith(("$2b$", "$2a$", "$2y$")):
            return bcrypt.checkpw(password.encode(), stored_hash.encode())
        # Legacy SHA-256 fallback
        return hashlib.sha256(password.encode()).hexdigest() == stored_hash
    except Exception:
        return False


def is_legacy_hash(stored_hash: str) -> bool:
    """Return True if the stored hash is a legacy SHA-256 hash."""
    return not stored_hash.startswith(("$2b$", "$2a$", "$2y$"))


def create_tables():
    """Creates all database tables if they don't already exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,
            full_name   TEXT    NOT NULL,
            role        TEXT    NOT NULL CHECK(role IN ('admin', 'manager', 'cashier')),
            is_active   INTEGER NOT NULL DEFAULT 1,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            product_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT    NOT NULL,
            category     TEXT    NOT NULL DEFAULT 'General',
            price        REAL    NOT NULL CHECK(price >= 0),
            barcode      TEXT    UNIQUE,
            supplier     TEXT,
            is_active    INTEGER NOT NULL DEFAULT 1,
            created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS inventory (
            inventory_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id      INTEGER NOT NULL UNIQUE,
            quantity        INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
            low_stock_alert INTEGER NOT NULL DEFAULT 5,
            last_updated    TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS inventory_transactions (
            transaction_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id        INTEGER NOT NULL,
            transaction_type  TEXT    NOT NULL CHECK(transaction_type IN ('add', 'remove', 'adjust')),
            quantity_change   INTEGER NOT NULL,
            previous_quantity INTEGER NOT NULL,
            new_quantity      INTEGER NOT NULL,
            reason            TEXT,
            user_id           INTEGER,
            transaction_date  TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (product_id) REFERENCES products(product_id),
            FOREIGN KEY (user_id)    REFERENCES users(user_id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            customer_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name      TEXT NOT NULL,
            phone          TEXT UNIQUE,
            email          TEXT,
            address        TEXT,
            loyalty_points INTEGER NOT NULL DEFAULT 0,
            created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sales (
            sale_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER NOT NULL,
            customer_id    INTEGER,
            total_amount   REAL    NOT NULL,
            discount       REAL    NOT NULL DEFAULT 0,
            tax            REAL    NOT NULL DEFAULT 0,
            payment_method TEXT    NOT NULL CHECK(payment_method IN ('cash', 'momo', 'card')),
            sale_date      TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id)     REFERENCES users(user_id),
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sale_items (
            sale_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id      INTEGER NOT NULL,
            product_id   INTEGER NOT NULL,
            quantity     INTEGER NOT NULL CHECK(quantity > 0),
            unit_price   REAL    NOT NULL,
            subtotal     REAL    NOT NULL,
            FOREIGN KEY (sale_id)    REFERENCES sales(sale_id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS payments (
            payment_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id        INTEGER NOT NULL,
            amount_paid    REAL    NOT NULL,
            change_given   REAL    NOT NULL DEFAULT 0,
            payment_method TEXT    NOT NULL CHECK(payment_method IN ('cash', 'momo', 'card', 'bank_transfer')),
            status         TEXT    NOT NULL DEFAULT 'completed'
                           CHECK(status IN ('pending', 'processing', 'completed', 'failed', 'reversed')),
            reference      TEXT,
            provider       TEXT,
            fee            REAL    NOT NULL DEFAULT 0,
            payment_date   TEXT    NOT NULL DEFAULT (datetime('now')),
            created_at     TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (sale_id) REFERENCES sales(sale_id) ON DELETE CASCADE
        )
    """
    )

    # Indexes
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_products_barcode    ON products(barcode)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_products_category   ON products(category)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_sales_date          ON sales(sale_date)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_sales_user          ON sales(user_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_inventory_low_stock ON inventory(quantity, low_stock_alert)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_payments_date       ON payments(payment_date)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_payments_method     ON payments(payment_method)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_payments_status     ON payments(payment_status)"
        if False
        else "CREATE INDEX IF NOT EXISTS idx_payments_status     ON payments(status)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_payments_sale       ON payments(sale_id)"
    )

    conn.commit()
    conn.close()
    logger.info("All tables created successfully.")


def seed_default_admin():
    """
    Seeds default accounts only if they do not already exist.

    Credentials are read from the environment so they are never
    hard-coded in source.  If the env vars are absent a secure
    random password is generated and printed once — copy it now.
    """
    defaults = {
        "admin": (
            os.getenv("DEFAULT_ADMIN_PASSWORD") or secrets.token_urlsafe(12),
            "System Administrator",
            "admin",
        ),
        "manager": (
            os.getenv("DEFAULT_MANAGER_PASSWORD") or secrets.token_urlsafe(12),
            "Store Manager",
            "manager",
        ),
        "cashier": (
            os.getenv("DEFAULT_CASHIER_PASSWORD") or secrets.token_urlsafe(12),
            "POS Cashier",
            "cashier",
        ),
    }

    with get_db_connection() as conn:
        cursor = conn.cursor()
        for username, (password, full_name, role) in defaults.items():
            cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
            if cursor.fetchone() is None:
                cursor.execute(
                    "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
                    (username, hash_password(password), full_name, role),
                )
                logger.warning(
                    "Seeded account: %s / %s (%s) — change this password immediately!",
                    username,
                    password,
                    role,
                )


def seed_sample_data():
    """Optional: seed sample products for testing."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] > 0:
            return

        sample_products = [
            ("Laptop", "Electronics", 999.99, "BAR001", "TechSupplier"),
            ("Mouse", "Electronics", 29.99, "BAR002", "TechSupplier"),
            ("Keyboard", "Electronics", 79.99, "BAR003", "TechSupplier"),
            ("Monitor", "Electronics", 299.99, "BAR004", "TechSupplier"),
            ("Printer", "Office", 199.99, "BAR005", "OfficeSupply"),
            ("Paper A4", "Office", 9.99, "BAR006", "OfficeSupply"),
            ("Desk", "Furniture", 249.99, "BAR007", "FurnitureCo"),
            ("Office Chair", "Furniture", 149.99, "BAR008", "FurnitureCo"),
        ]

        for product in sample_products:
            cursor.execute(
                "INSERT INTO products (product_name, category, price, barcode, supplier) VALUES (?,?,?,?,?)",
                product,
            )
            product_id = cursor.lastrowid
            quantity = 50 if product[1] == "Office" else 20
            cursor.execute(
                "INSERT INTO inventory (product_id, quantity, low_stock_alert) VALUES (?,?,?)",
                (product_id, quantity, 10),
            )
        logger.info("Sample products seeded.")


def initialize_database(with_sample_data: bool = False):
    """Full database setup: create tables + seed defaults + optional sample data."""
    create_tables()

    # Add this import and call
    from database.migrate import run_migrations

    with get_db_connection() as conn:
        run_migrations(conn)

    seed_default_admin()
    if with_sample_data:
        seed_sample_data()


# ── Helper functions ──────────────────────────────────────────────────────────


def execute_query(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def execute_insert(query: str, params: tuple = ()) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.lastrowid


def execute_update(query: str, params: tuple = ()) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.rowcount


def get_product_with_inventory(product_id: int) -> Optional[Dict[str, Any]]:
    query = """
        SELECT p.*, i.quantity, i.low_stock_alert, i.last_updated
        FROM products p
        LEFT JOIN inventory i ON p.product_id = i.product_id
        WHERE p.product_id = ? AND p.is_active = 1
    """
    results = execute_query(query, (product_id,))
    return results[0] if results else None


def update_inventory(
    product_id: int, quantity_change: int, reason: str, user_id: int = None
) -> bool:
    """Update inventory with full audit trail. quantity_change: + for add, - for remove."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT quantity FROM inventory WHERE product_id = ?", (product_id,)
            )
            result = cursor.fetchone()

            if not result:
                cursor.execute(
                    "INSERT INTO inventory (product_id, quantity, low_stock_alert) VALUES (?,?,?)",
                    (product_id, max(0, quantity_change), 5),
                )
                current_qty = 0
            else:
                current_qty = result[0]

            new_qty = current_qty + quantity_change
            if new_qty < 0:
                return False

            cursor.execute(
                "UPDATE inventory SET quantity = ?, last_updated = datetime('now') WHERE product_id = ?",
                (new_qty, product_id),
            )

            transaction_type = (
                "add"
                if quantity_change > 0
                else "remove"
                if quantity_change < 0
                else "adjust"
            )
            cursor.execute(
                """INSERT INTO inventory_transactions
                   (product_id, transaction_type, quantity_change, previous_quantity, new_quantity, reason, user_id)
                   VALUES (?,?,?,?,?,?,?)""",
                (
                    product_id,
                    transaction_type,
                    abs(quantity_change),
                    current_qty,
                    new_qty,
                    reason,
                    user_id,
                ),
            )
            return True
    except Exception as e:
        logger.error("Error updating inventory for product %s: %s", product_id, e)
        return False


def get_low_stock_products(threshold: int = None) -> List[Dict[str, Any]]:
    query = """
        SELECT p.product_id, p.product_name, p.category, p.price,
               i.quantity, i.low_stock_alert
        FROM products p
        JOIN inventory i ON p.product_id = i.product_id
        WHERE p.is_active = 1 AND i.quantity <= i.low_stock_alert
        ORDER BY i.quantity ASC
    """
    return execute_query(query)


if __name__ == "__main__":
    initialize_database(with_sample_data=True)
    conn = get_connection()
    cursor = conn.cursor()
    print("\n── Tables ──")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    for row in cursor.fetchall():
        print(f"  ✓ {row['name']}")
    print("\n── Users ──")
    cursor.execute("SELECT user_id, username, full_name, role FROM users")
    for row in cursor.fetchall():
        print(f"  {row['user_id']}  {row['username']}  {row['role']}")
    conn.close()
    print("\n[DB] Ready.")
