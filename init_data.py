"""
Initialize the database with demo data for testing
"""

from database.db import initialize_database, get_connection
from database.db import hash_password

def add_demo_data():
    """Add demo products, customers, and users"""
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if we already have products
    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("Adding demo products...")
        
        # Demo products
        demo_products = [
            ("Laptop Pro", "Electronics", 1299.99, "BAR001", "TechSupplier", 15),
            ("Wireless Mouse", "Electronics", 29.99, "BAR002", "TechSupplier", 50),
            ("Mechanical Keyboard", "Electronics", 89.99, "BAR003", "TechSupplier", 30),
            ("27-inch Monitor", "Electronics", 299.99, "BAR004", "TechSupplier", 12),
            ("Office Desk", "Furniture", 199.99, "BAR005", "FurnitureCo", 8),
            ("Ergonomic Chair", "Furniture", 249.99, "BAR006", "FurnitureCo", 10),
            ("Printer", "Office", 149.99, "BAR007", "OfficeSupply", 5),
            ("A4 Paper (500 sheets)", "Office", 12.99, "BAR008", "OfficeSupply", 100),
            ("Coffee Mug", "Accessories", 9.99, "BAR009", "AccessoryWorld", 45),
            ("Notebook", "Stationery", 4.99, "BAR010", "StationeryPlus", 80),
        ]
        
        for product in demo_products:
            cursor.execute("""
                INSERT INTO products (product_name, category, price, barcode, supplier)
                VALUES (?, ?, ?, ?, ?)
            """, (product[0], product[1], product[2], product[3], product[4]))
            
            product_id = cursor.lastrowid
            
            cursor.execute("""
                INSERT INTO inventory (product_id, quantity, low_stock_alert)
                VALUES (?, ?, ?)
            """, (product_id, product[5], 10))
        
        print(f"✓ Added {len(demo_products)} demo products")
    
    # Add demo customers
    cursor.execute("SELECT COUNT(*) FROM customers")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("Adding demo customers...")
        
        demo_customers = [
            ("John Doe", "1234567890", "john@example.com", "123 Main St", 150),
            ("Jane Smith", "0987654321", "jane@example.com", "456 Oak Ave", 250),
            ("Bob Johnson", "5551234567", "bob@example.com", "789 Pine Rd", 75),
            ("Alice Brown", "4449876543", "alice@example.com", "321 Elm St", 500),
            ("Charlie Wilson", "7775558888", "charlie@example.com", "654 Maple Dr", 30),
        ]
        
        for customer in demo_customers:
            cursor.execute("""
                INSERT INTO customers (full_name, phone, email, address, loyalty_points)
                VALUES (?, ?, ?, ?, ?)
            """, customer)
        
        print(f"✓ Added {len(demo_customers)} demo customers")
    
    # Add sample sales (last 7 days)
    from datetime import datetime, timedelta
    
    cursor.execute("SELECT COUNT(*) FROM sales")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("Adding sample sales data...")
        
        # Get users
        cursor.execute("SELECT user_id FROM users WHERE role = 'cashier' LIMIT 1")
        cashier = cursor.fetchone()
        if cashier:
            user_id = cashier['user_id']
        else:
            user_id = 1
        
        # Get products
        cursor.execute("SELECT product_id, price FROM products LIMIT 5")
        products = cursor.fetchall()
        
        # Create sales for the last 7 days
        for day in range(7):
            sale_date = (datetime.now() - timedelta(days=day)).strftime('%Y-%m-%d')
            
            # Create 2-5 sales per day
            for _ in range(3):
                # Random number of items
                import random
                num_items = random.randint(1, 3)
                total = 0
                
                cursor.execute("""
                    INSERT INTO sales (user_id, total_amount, payment_method, sale_date)
                    VALUES (?, ?, ?, ?)
                """, (user_id, 0, random.choice(['cash', 'momo', 'card']), sale_date))
                
                sale_id = cursor.lastrowid
                
                for i in range(num_items):
                    product = random.choice(products)
                    quantity = random.randint(1, 2)
                    subtotal = product['price'] * quantity
                    total += subtotal
                    
                    cursor.execute("""
                        INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, subtotal)
                        VALUES (?, ?, ?, ?, ?)
                    """, (sale_id, product['product_id'], quantity, product['price'], subtotal))
                
                # Update sale total
                cursor.execute("UPDATE sales SET total_amount = ? WHERE sale_id = ?", (total, sale_id))
                
                # Add payment
                cursor.execute("""
                    INSERT INTO payments (sale_id, amount_paid, change_given, payment_method)
                    VALUES (?, ?, ?, ?)
                """, (sale_id, total, 0, random.choice(['cash', 'momo', 'card'])))
        
        print(f"✓ Added sample sales data")
    
    conn.commit()
    conn.close()
    print("\n✓ Demo data added successfully!")

if __name__ == "__main__":
    print("=" * 50)
    print("POS System - Database Initialization")
    print("=" * 50)
    
    # Initialize database
    print("\nInitializing database...")
    initialize_database()
    
    # Add demo data
    add_demo_data()
    
    print("\n" + "=" * 50)
    print("Setup complete! You can now run the POS system.")
    print("=" * 50)
    print("\nLogin Credentials:")
    print("  Admin:   admin / admin123")
    print("  Manager: manager / manager123")
    print("  Cashier: cashier / cashier123")
    print("\n")