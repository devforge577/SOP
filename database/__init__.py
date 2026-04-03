"""
Database module for POS System.
Handles connections, schema creation, migrations, and core operations.
"""

from .db import (
    get_connection,
    get_db_connection,
    hash_password,
    verify_password,
    create_tables,
    initialize_database,
    execute_query,
    execute_insert,
    execute_update,
    get_product_with_inventory,
    update_inventory,
    get_low_stock_products,
)

from .migrate import run_migrations, migration_status

__all__ = [
    # Connection
    "get_connection",
    "get_db_connection",
    # Auth helpers
    "hash_password",
    "verify_password",
    # Schema
    "create_tables",
    "initialize_database",
    # Migrations
    "run_migrations",
    "migration_status",
    # Query helpers
    "execute_query",
    "execute_insert",
    "execute_update",
    # Business logic
    "get_product_with_inventory",
    "update_inventory",
    "get_low_stock_products",
]
