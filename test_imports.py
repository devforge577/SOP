#!/usr/bin/env python3
"""Test script to check if web server starts correctly."""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing imports...")
    from config import config
    print("✓ Config imported successfully")

    from database.db import get_connection
    print("✓ Database module imported successfully")

    # Test database connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    conn.close()
    print(f"✓ Database connection works: {result}")

    from web_server import app
    print("✓ Web server imported successfully")

    print("\n🎉 All imports successful! Web server should work.")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)