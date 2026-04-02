-- Migration 0001: Baseline schema
-- Captures the existing live database structure.
-- This migration is skipped automatically if the tables already exist.

CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT    NOT NULL UNIQUE,
    password    TEXT    NOT NULL,
    full_name   TEXT    NOT NULL,
    role        TEXT    NOT NULL CHECK(role IN ('admin', 'manager', 'cashier')),
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS products (
    product_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT    NOT NULL,
    category     TEXT    NOT NULL DEFAULT 'General',
    price        REAL    NOT NULL CHECK(price >= 0),
    barcode      TEXT    UNIQUE,
    supplier     TEXT,
    is_active    INTEGER NOT NULL DEFAULT 1,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS inventory (
    inventory_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      INTEGER NOT NULL UNIQUE,
    quantity        INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
    low_stock_alert INTEGER NOT NULL DEFAULT 5,
    last_updated    TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

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
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name      TEXT NOT NULL,
    phone          TEXT UNIQUE,
    email          TEXT,
    address        TEXT,
    loyalty_points INTEGER NOT NULL DEFAULT 0,
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

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
);

CREATE TABLE IF NOT EXISTS sale_items (
    sale_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id      INTEGER NOT NULL,
    product_id   INTEGER NOT NULL,
    quantity     INTEGER NOT NULL CHECK(quantity > 0),
    unit_price   REAL    NOT NULL,
    subtotal     REAL    NOT NULL,
    FOREIGN KEY (sale_id)    REFERENCES sales(sale_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id        INTEGER NOT NULL,
    amount_paid    REAL    NOT NULL,
    change_given   REAL    NOT NULL DEFAULT 0,
    payment_method TEXT    NOT NULL CHECK(payment_method IN ('cash', 'momo', 'card', 'bank_transfer')),
    status         TEXT    NOT NULL DEFAULT 'completed' CHECK(status IN ('pending', 'processing', 'completed', 'failed', 'reversed')),
    reference      TEXT,
    provider       TEXT,
    fee            REAL    NOT NULL DEFAULT 0,
    payment_date   TEXT    NOT NULL DEFAULT (datetime('now')),
    created_at     TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (sale_id) REFERENCES sales(sale_id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_products_barcode    ON products(barcode);
CREATE INDEX IF NOT EXISTS idx_products_category   ON products(category);
CREATE INDEX IF NOT EXISTS idx_sales_date          ON sales(sale_date);
CREATE INDEX IF NOT EXISTS idx_sales_user          ON sales(user_id);
CREATE INDEX IF NOT EXISTS idx_inventory_low_stock ON inventory(quantity, low_stock_alert);
CREATE INDEX IF NOT EXISTS idx_payments_date       ON payments(payment_date);
CREATE INDEX IF NOT EXISTS idx_payments_method     ON payments(payment_method);
CREATE INDEX IF NOT EXISTS idx_payments_status     ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_sale       ON payments(sale_id);