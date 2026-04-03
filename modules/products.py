from database.db import (
    get_connection,
    update_inventory,
    get_low_stock_products as db_get_low_stock,
)
from typing import Optional, List, Dict, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_all_products(include_inactive: bool = False) -> List[Dict]:
    """Returns all products. Set include_inactive=True to see deleted products too."""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT p.product_id, p.product_name, p.category, p.price,
               p.barcode, p.supplier, p.is_active, p.created_at,
               COALESCE(i.quantity, 0) AS stock,
               i.low_stock_alert, i.last_updated
        FROM products p
        LEFT JOIN inventory i ON p.product_id = i.product_id
    """
    if not include_inactive:
        query += " WHERE p.is_active = 1"
    query += " ORDER BY p.category, p.product_name"

    cursor.execute(query)
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return products


def search_products(keyword: str) -> List[Dict]:
    """Search products by name, category, or barcode."""
    conn = get_connection()
    cursor = conn.cursor()
    like = f"%{keyword.strip()}%"
    cursor.execute(
        """
        SELECT p.product_id, p.product_name, p.category, p.price,
               p.barcode, p.supplier, p.is_active,
               COALESCE(i.quantity, 0) AS stock,
               i.low_stock_alert
        FROM products p
        LEFT JOIN inventory i ON p.product_id = i.product_id
        WHERE p.is_active = 1
          AND (p.product_name LIKE ? OR p.category LIKE ? OR p.barcode LIKE ?)
        ORDER BY p.product_name
    """,
        (like, like, like),
    )
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return products


def get_product_by_barcode(barcode: str) -> Optional[Dict]:
    """Fetch a single product by barcode (used when scanning)."""
    if not barcode or not barcode.strip():
        return None

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT p.product_id, p.product_name, p.category, p.price,
               p.barcode, p.supplier, COALESCE(i.quantity, 0) AS stock,
               i.low_stock_alert
        FROM products p
        LEFT JOIN inventory i ON p.product_id = i.product_id
        WHERE p.barcode = ? AND p.is_active = 1
    """,
        (barcode.strip(),),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_product_by_id(product_id: int) -> Optional[Dict]:
    """Fetch a single product by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT p.product_id, p.product_name, p.category, p.price,
               p.barcode, p.supplier, COALESCE(i.quantity, 0) AS stock,
               i.low_stock_alert
        FROM products p
        LEFT JOIN inventory i ON p.product_id = i.product_id
        WHERE p.product_id = ? AND p.is_active = 1
    """,
        (product_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def add_product(
    product_name: str,
    category: str,
    price: float,
    barcode: str = None,
    supplier: str = None,
    initial_stock: int = 0,
    low_stock_alert: int = 5,
    user_id: int = None,
) -> Tuple[bool, str]:
    """
    Adds a new product and creates its inventory record.
    Returns (True, "success") or (False, "error message").
    """
    # Validation
    if not product_name or not product_name.strip():
        return False, "Product name cannot be empty."
    if price < 0:
        return False, "Price cannot be negative."
    if initial_stock < 0:
        return False, "Initial stock cannot be negative."
    if low_stock_alert < 0:
        return False, "Low stock alert cannot be negative."

    # Clean inputs
    product_name = product_name.strip()
    category = category.strip() or "General"
    barcode = barcode.strip() if barcode and barcode.strip() else None
    supplier = supplier.strip() if supplier and supplier.strip() else None

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Insert product
        cursor.execute(
            """
            INSERT INTO products (product_name, category, price, barcode, supplier)
            VALUES (?, ?, ?, ?, ?)
        """,
            (product_name, category, price, barcode, supplier),
        )
        product_id = cursor.lastrowid

        # Create matching inventory record
        cursor.execute(
            """
            INSERT INTO inventory (product_id, quantity, low_stock_alert)
            VALUES (?, ?, ?)
        """,
            (product_id, initial_stock, low_stock_alert),
        )

        # Log initial stock addition if any
        if initial_stock > 0:
            update_inventory(product_id, initial_stock, "Initial stock", user_id)

        conn.commit()
        logger.info(f"Product added: {product_name} (ID: {product_id})")
        return True, f"Product added successfully (ID: {product_id})"
    except Exception as e:
        conn.rollback()
        if "UNIQUE" in str(e):
            return False, "A product with that barcode already exists."
        logger.error(f"Error adding product: {e}")
        return False, f"Error adding product: {str(e)}"
    finally:
        conn.close()


def update_product(
    product_id: int,
    product_name: str = None,
    category: str = None,
    price: float = None,
    barcode: str = None,
    supplier: str = None,
    low_stock_alert: int = None,
    user_id: int = None,
) -> Tuple[bool, str]:
    """
    Updates an existing product's details.
    Returns (True, "success") or (False, "error message").
    """
    updates = []
    params = []

    if product_name is not None:
        if not product_name.strip():
            return False, "Product name cannot be empty."
        updates.append("product_name = ?")
        params.append(product_name.strip())

    if category is not None:
        updates.append("category = ?")
        params.append(category.strip() or "General")

    if price is not None:
        if price < 0:
            return False, "Price cannot be negative."
        updates.append("price = ?")
        params.append(price)

    if barcode is not None:
        params.append(barcode.strip() if barcode.strip() else None)
        updates.append("barcode = ?")

    if supplier is not None:
        params.append(supplier.strip() if supplier.strip() else None)
        updates.append("supplier = ?")

    if not updates:
        return False, "No fields to update"

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Update product
        if updates:
            params.append(product_id)
            cursor.execute(
                f"""
                UPDATE products
                SET {', '.join(updates)}
                WHERE product_id = ?
            """,
                params,
            )

        # Update inventory alert level if provided
        if low_stock_alert is not None:
            if low_stock_alert < 0:
                return False, "Low stock alert cannot be negative."
            cursor.execute(
                """
                UPDATE inventory SET low_stock_alert = ?
                WHERE product_id = ?
            """,
                (low_stock_alert, product_id),
            )

        conn.commit()
        logger.info(f"Product {product_id} updated")
        return True, "Product updated successfully."
    except Exception as e:
        conn.rollback()
        if "UNIQUE" in str(e):
            return False, "A product with that barcode already exists."
        logger.error(f"Error updating product: {e}")
        return False, f"Error updating product: {str(e)}"
    finally:
        conn.close()


def delete_product(product_id: int) -> Tuple[bool, str]:
    """
    Soft-deletes a product (sets is_active = 0).
    Products are never hard-deleted to preserve sales history.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check if product has sales records
        cursor.execute(
            "SELECT COUNT(*) FROM sale_items WHERE product_id = ?", (product_id,)
        )
        sales_count = cursor.fetchone()[0]

        if sales_count > 0:
            # Soft delete only if product has been sold
            cursor.execute(
                """
                UPDATE products SET is_active = 0 WHERE product_id = ?
            """,
                (product_id,),
            )
            conn.commit()
            logger.info(
                f"Product {product_id} deactivated (has {sales_count} sales records)"
            )
            return True, "Product deactivated successfully."
        else:
            # Can hard delete if never sold
            cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
            cursor.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
            conn.commit()
            logger.info(f"Product {product_id} permanently deleted (no sales history)")
            return True, "Product permanently deleted."
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        return False, f"Error deleting product: {str(e)}"
    finally:
        conn.close()


def restore_product(product_id: int) -> Tuple[bool, str]:
    """Restore a soft-deleted product"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE products SET is_active = 1 WHERE product_id = ?
        """,
            (product_id,),
        )
        conn.commit()
        logger.info(f"Product {product_id} restored")
        return True, "Product restored successfully."
    except Exception as e:
        logger.error(f"Error restoring product: {e}")
        return False, f"Error restoring product: {str(e)}"
    finally:
        conn.close()


def get_categories() -> List[str]:
    """Returns a sorted list of all unique product categories."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT DISTINCT category FROM products
        WHERE is_active = 1 ORDER BY category
    """
    )
    categories = [row["category"] for row in cursor.fetchall()]
    conn.close()
    return categories


def get_low_stock_products() -> List[Dict]:
    """Returns products where stock is at or below the low_stock_alert threshold."""
    return db_get_low_stock()


def adjust_stock(
    product_id: int,
    quantity_change: int,
    reason: str = "Manual adjustment",
    user_id: int = None,
) -> Tuple[bool, int]:
    """
    Adjusts stock by a delta. Use positive to add, negative to deduct.
    Returns (True, new_quantity) or (False, "error message").
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT quantity FROM inventory WHERE product_id = ?
        """,
            (product_id,),
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            return False, "Product not found in inventory."

        new_qty = row["quantity"] + quantity_change
        if new_qty < 0:
            conn.close()
            return False, f"Insufficient stock. Current stock: {row['quantity']}"

        # Update inventory using the transaction logging function
        success = update_inventory(product_id, quantity_change, reason, user_id)

        if success:
            logger.info(
                f"Stock adjusted for product {product_id}: {quantity_change} units, new quantity: {new_qty}"
            )
            return True, new_qty
        else:
            return False, "Failed to update inventory"
    except Exception as e:
        logger.error(f"Error adjusting stock: {e}")
        return False, str(e)
    finally:
        conn.close()


def get_product_with_details(product_id: int) -> Optional[Dict]:
    """Get complete product details including inventory and sales stats"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT p.*,
               i.quantity, i.low_stock_alert, i.last_updated,
               (SELECT COUNT(*) FROM sale_items WHERE product_id = ?) as total_sold,
               (SELECT SUM(quantity) FROM sale_items WHERE product_id = ?) as total_quantity_sold
        FROM products p
        LEFT JOIN inventory i ON p.product_id = i.product_id
        WHERE p.product_id = ?
    """,
        (product_id, product_id, product_id),
    )

    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_products_by_category(category: str) -> List[Dict]:
    """Get all products in a specific category"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT p.product_id, p.product_name, p.price,
               COALESCE(i.quantity, 0) AS stock
        FROM products p
        LEFT JOIN inventory i ON p.product_id = i.product_id
        WHERE p.category = ? AND p.is_active = 1
        ORDER BY p.product_name
    """,
        (category,),
    )
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return products


def bulk_import_products(
    products_list: List[Dict], user_id: int = None
) -> Tuple[bool, str, int]:
    """
    Bulk import multiple products
    Returns (success, message, count_imported)
    """
    imported = 0
    errors = []

    for product in products_list:
        try:
            success, msg = add_product(
                product_name=product.get("name"),
                category=product.get("category", "General"),
                price=product.get("price", 0),
                barcode=product.get("barcode"),
                supplier=product.get("supplier"),
                initial_stock=product.get("stock", 0),
                low_stock_alert=product.get("low_stock_alert", 5),
                user_id=user_id,
            )
            if success:
                imported += 1
            else:
                errors.append(f"{product.get('name')}: {msg}")
        except Exception as e:
            errors.append(f"{product.get('name')}: {str(e)}")

    if errors:
        return (
            False,
            f"Imported {imported} products. Errors: {'; '.join(errors[:5])}",
            imported,
        )
    return True, f"Successfully imported {imported} products", imported


# ── Quick test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Test adding a product
    success, msg = add_product(
        "Test Product", "Test Category", 19.99, "TEST001", "Test Supplier", 100
    )
    print(f"Add product: {msg}")

    # Get all products
    products = get_all_products()
    print(f"\nTotal products: {len(products)}")
    for p in products[:5]:  # Show first 5
        print(f"  {p['product_name']} - ${p['price']} - Stock: {p['stock']}")

    # Check low stock
    low_stock = get_low_stock_products()
    print(f"\nLow stock products: {len(low_stock)}")


class ProductManager:
    """Convenience wrapper around product functions."""

    def __init__(self, auth=None):
        self.auth = auth

    def get_all_products(self, include_inactive=False):
        return get_all_products(include_inactive)

    def search_products(self, keyword):
        return search_products(keyword)

    def get_product_by_barcode(self, barcode):
        return get_product_by_barcode(barcode)

    def get_product_by_id(self, product_id):
        return get_product_by_id(product_id)

    def add_product(self, *args, **kwargs):
        return add_product(*args, **kwargs)

    def update_product(self, *args, **kwargs):
        return update_product(*args, **kwargs)

    def delete_product(self, *args, **kwargs):
        return delete_product(*args, **kwargs)

    def restore_product(self, *args, **kwargs):
        return restore_product(*args, **kwargs)

    def get_categories(self):
        return get_categories()

    def get_low_stock_products(self):
        return get_low_stock_products()

    def adjust_stock(self, *args, **kwargs):
        return adjust_stock(*args, **kwargs)

    def get_product_with_details(self, product_id):
        return get_product_with_details(product_id)

    def get_products_by_category(self, category):
        return get_products_by_category(category)

    def bulk_import_products(self, products_list, user_id=None):
        return bulk_import_products(products_list, user_id)


# ── Quick test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Test adding a product
    success, msg = add_product(
        "Test Product", "Test Category", 19.99, "TEST001", "Test Supplier", 100
    )
    print(f"Add product: {msg}")

    # Get all products
    products = get_all_products()
    print(f"\nTotal products: {len(products)}")
    for p in products[:5]:  # Show first 5
        print(f"  {p['product_name']} - ${p['price']} - Stock: {p['stock']}")

    # Check low stock
    low_stock = get_low_stock_products()
    print(f"\nLow stock products: {len(low_stock)}")
