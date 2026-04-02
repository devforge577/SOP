"""
Database Migration Script - Add Payment System Columns

This script adds the new payment tracking columns to the existing payments table
without losing any data.
"""

import sqlite3
from database.db import get_connection

def migrate_payment_table():
    """Add new columns to payments table"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get current columns
        cursor.execute("PRAGMA table_info(payments)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        print(f"Existing columns: {existing_columns}")
        
        # Add missing columns one by one
        new_columns = {
            'status': "ALTER TABLE payments ADD COLUMN status TEXT DEFAULT 'completed'",
            'reference': "ALTER TABLE payments ADD COLUMN reference TEXT",
            'provider': "ALTER TABLE payments ADD COLUMN provider TEXT",
            'fee': "ALTER TABLE payments ADD COLUMN fee REAL DEFAULT 0",
            'created_at': "ALTER TABLE payments ADD COLUMN created_at TEXT"
        }
        
        for col_name, sql in new_columns.items():
            if col_name not in existing_columns:
                try:
                    cursor.execute(sql)
                    print(f"[OK] Added column: {col_name}")
                except sqlite3.OperationalError as e:
                    if 'already exists' in str(e):
                        print(f"[SKIP] Column {col_name} already exists")
                    else:
                        raise
        
        # Add new indexes
        indexes = [
            ("idx_payments_date", "CREATE INDEX IF NOT EXISTS idx_payments_date ON payments(payment_date)"),
            ("idx_payments_method", "CREATE INDEX IF NOT EXISTS idx_payments_method ON payments(payment_method)"),
            ("idx_payments_status", "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)"),
            ("idx_payments_sale", "CREATE INDEX IF NOT EXISTS idx_payments_sale ON payments(sale_id)")
        ]
        
        for idx_name, sql in indexes:
            try:
                cursor.execute(sql)
                print(f"[OK] Created index: {idx_name}")
            except sqlite3.OperationalError as e:
                print(f"[SKIP] Index {idx_name}: {e}")
        
        conn.commit()
        print("\n[SUCCESS] Database migration complete!")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("Starting database migration...")
    migrate_payment_table()
