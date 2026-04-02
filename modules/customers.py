from database.db import get_connection, get_db_connection
from typing import Optional, Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ── CRUD ──────────────────────────────────────────────────────────────────────

def add_customer(full_name: str, phone: str = None,
                 email: str = None, address: str = None) -> Tuple[bool, str]:
    """Register a new customer. Phone must be unique if provided."""
    if not full_name or not full_name.strip():
        return False, "Full name cannot be empty."

    full_name = full_name.strip()
    phone     = phone.strip()   if phone   and phone.strip()   else None
    email     = email.strip()   if email   and email.strip()   else None
    address   = address.strip() if address and address.strip() else None

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO customers (full_name, phone, email, address)
                VALUES (?, ?, ?, ?)
            """, (full_name, phone, email, address))
            customer_id = cursor.lastrowid
            logger.info(f"Customer added: {full_name} (ID: {customer_id})")
            return True, f"Customer registered successfully (ID: {customer_id})."
    except Exception as e:
        if "UNIQUE" in str(e):
            return False, "A customer with that phone number already exists."
        logger.error(f"Error adding customer: {e}")
        return False, f"Error adding customer: {str(e)}"


def get_customer_by_phone(phone: str) -> Optional[Dict]:
    """Look up a customer by phone number."""
    if not phone or not phone.strip():
        return None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT customer_id, full_name, phone, email, address, loyalty_points, created_at
            FROM customers
            WHERE phone = ?
        """, (phone.strip(),))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error finding customer by phone: {e}")
        return None


def get_customer_by_id(customer_id: int) -> Optional[Dict]:
    """Fetch a customer by ID."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT customer_id, full_name, phone, email, address, loyalty_points, created_at
            FROM customers
            WHERE customer_id = ?
        """, (customer_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error fetching customer {customer_id}: {e}")
        return None


def search_customers(keyword: str) -> List[Dict]:
    """Search customers by name or phone."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        like = f"%{keyword.strip()}%"
        cursor.execute("""
            SELECT customer_id, full_name, phone, email, loyalty_points
            FROM customers
            WHERE full_name LIKE ? OR phone LIKE ?
            ORDER BY full_name
        """, (like, like))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        logger.error(f"Error searching customers: {e}")
        return []


def get_all_customers() -> List[Dict]:
    """Return all registered customers."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT customer_id, full_name, phone, email, address, loyalty_points, created_at
            FROM customers
            ORDER BY full_name
        """)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        logger.error(f"Error fetching all customers: {e}")
        return []


def update_customer(customer_id: int, full_name: str = None,
                    phone: str = None, email: str = None,
                    address: str = None) -> Tuple[bool, str]:
    """Update customer details."""
    updates, params = [], []

    if full_name is not None:
        if not full_name.strip():
            return False, "Full name cannot be empty."
        updates.append("full_name = ?")
        params.append(full_name.strip())
    if phone is not None:
        updates.append("phone = ?")
        params.append(phone.strip() or None)
    if email is not None:
        updates.append("email = ?")
        params.append(email.strip() or None)
    if address is not None:
        updates.append("address = ?")
        params.append(address.strip() or None)

    if not updates:
        return False, "No fields to update."

    params.append(customer_id)
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE customers SET {', '.join(updates)} WHERE customer_id = ?",
                params
            )
            if cursor.rowcount == 0:
                return False, "Customer not found."
            logger.info(f"Customer {customer_id} updated.")
            return True, "Customer updated successfully."
    except Exception as e:
        if "UNIQUE" in str(e):
            return False, "A customer with that phone number already exists."
        logger.error(f"Error updating customer: {e}")
        return False, f"Error updating customer: {str(e)}"


def delete_customer(customer_id: int) -> Tuple[bool, str]:
    """
    Soft-delete by nulling personal fields, or hard-delete if no sales history.
    Customer rows are kept to preserve sales history.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sales WHERE customer_id = ?", (customer_id,))
        sales_count = cursor.fetchone()[0]
        conn.close()

        if sales_count > 0:
            # Anonymise instead of deleting
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE customers
                    SET full_name = 'Deleted Customer', phone = NULL,
                        email = NULL, address = NULL
                    WHERE customer_id = ?
                """, (customer_id,))
            logger.info(f"Customer {customer_id} anonymised ({sales_count} sales preserved).")
            return True, "Customer data removed (sales history preserved)."
        else:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM customers WHERE customer_id = ?", (customer_id,))
            logger.info(f"Customer {customer_id} permanently deleted.")
            return True, "Customer permanently deleted."
    except Exception as e:
        logger.error(f"Error deleting customer: {e}")
        return False, f"Error deleting customer: {str(e)}"


# ── Loyalty points ─────────────────────────────────────────────────────────────

# 1 loyalty point awarded for every 1 GHS spent (rounded down).
POINTS_PER_GHS = 1
POINTS_REDEEM_VALUE = 0.01   # 1 point = GHS 0.01 when redeemed


def award_loyalty_points(customer_id: int, amount_spent: float) -> int:
    """
    Award loyalty points based on amount spent.
    Returns the number of points awarded (0 if no customer).
    """
    if not customer_id:
        return 0

    points = int(amount_spent * POINTS_PER_GHS)
    if points <= 0:
        return 0

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE customers
                SET loyalty_points = loyalty_points + ?
                WHERE customer_id = ?
            """, (points, customer_id))
            if cursor.rowcount == 0:
                return 0
            logger.info(f"Awarded {points} points to customer {customer_id}")
            return points
    except Exception as e:
        logger.error(f"Error awarding loyalty points: {e}")
        return 0


def redeem_loyalty_points(customer_id: int,
                           points_to_redeem: int) -> Tuple[bool, float, str]:
    """
    Redeem loyalty points as a discount.
    Returns (success, discount_amount_GHS, message).
    """
    if not customer_id or points_to_redeem <= 0:
        return False, 0.0, "Invalid redemption request."

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT loyalty_points FROM customers WHERE customer_id = ?",
            (customer_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return False, 0.0, "Customer not found."

        available = row["loyalty_points"]
        if points_to_redeem > available:
            return False, 0.0, f"Insufficient points. Available: {available}"

        discount = round(points_to_redeem * POINTS_REDEEM_VALUE, 2)

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE customers
                SET loyalty_points = loyalty_points - ?
                WHERE customer_id = ?
            """, (points_to_redeem, customer_id))

        logger.info(
            f"Redeemed {points_to_redeem} points (GHS {discount:.2f}) "
            f"for customer {customer_id}"
        )
        return True, discount, f"Redeemed {points_to_redeem} pts for GHS {discount:.2f} discount."
    except Exception as e:
        logger.error(f"Error redeeming loyalty points: {e}")
        return False, 0.0, f"Error: {str(e)}"


def get_loyalty_balance(customer_id: int) -> int:
    """Return current loyalty point balance for a customer."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT loyalty_points FROM customers WHERE customer_id = ?",
            (customer_id,)
        )
        row = cursor.fetchone()
        conn.close()
        return row["loyalty_points"] if row else 0
    except Exception as e:
        logger.error(f"Error getting loyalty balance: {e}")
        return 0


def get_customer_purchase_history(customer_id: int) -> List[Dict]:
    """Return full sales history for a customer."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.sale_id, s.sale_date, s.total_amount,
                   s.payment_method, s.discount,
                   u.full_name AS cashier,
                   COUNT(si.sale_item_id) AS item_count
            FROM sales s
            JOIN users u ON s.user_id = u.user_id
            LEFT JOIN sale_items si ON s.sale_id = si.sale_id
            WHERE s.customer_id = ?
            GROUP BY s.sale_id
            ORDER BY s.sale_date DESC
        """, (customer_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        logger.error(f"Error fetching purchase history for {customer_id}: {e}")
        return []


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ok, msg = add_customer("Kwame Mensah", "0244000001", "kwame@email.com")
    print(f"Add: {msg}")

    c = get_customer_by_phone("0244000001")
    print(f"Found: {c}")

    if c:
        pts = award_loyalty_points(c["customer_id"], 150.0)
        print(f"Awarded {pts} points")

        bal = get_loyalty_balance(c["customer_id"])
        print(f"Balance: {bal} points")

        ok2, disc, msg2 = redeem_loyalty_points(c["customer_id"], 50)
        print(f"Redeem: {msg2} — discount GHS {disc:.2f}")