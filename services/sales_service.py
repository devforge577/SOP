"""
Sales Service

Handles sales and transaction operations including cart management.
"""

from typing import List, Dict, Tuple, Optional
from modules.sales import (
    SalesProcessor,
    cart_add_item,
    cart_remove_item,
    cart_update_quantity,
    cart_clear,
    cart_totals,
    process_sale,
    get_cart_item_count,
    generate_receipt,
)
import logging

logger = logging.getLogger(__name__)


class SalesService:
    """Service layer for sales operations."""

    def __init__(self, auth_service=None, product_service=None):
        self.sales_processor = SalesProcessor()
        self.auth_service = auth_service
        self.product_service = product_service

    def create_cart(self) -> List[Dict]:
        return []

    def add_to_cart(
        self, cart: List[Dict], product: Dict, quantity: int = 1
    ) -> Tuple[List[Dict], bool, str]:
        try:
            return cart_add_item(cart, product, quantity)
        except Exception as e:
            logger.error("Error adding to cart: %s", e)
            return cart, False, f"Error: {str(e)}"

    def remove_from_cart(self, cart: List[Dict], product_id: int) -> List[Dict]:
        try:
            return cart_remove_item(cart, product_id)
        except Exception as e:
            logger.error("Error removing from cart: %s", e)
            return cart

    def update_cart_quantity(
        self, cart: List[Dict], product_id: int, new_qty: int
    ) -> Tuple[List[Dict], bool, str]:
        try:
            return cart_update_quantity(cart, product_id, new_qty)
        except Exception as e:
            logger.error("Error updating cart: %s", e)
            return cart, False, f"Error: {str(e)}"

    def clear_cart(self, cart: List[Dict]) -> List[Dict]:
        try:
            return cart_clear(cart)
        except Exception as e:
            logger.error("Error clearing cart: %s", e)
            return cart

    def get_cart_totals(
        self, cart: List[Dict], discount: float = 0.0, tax_rate: float = 0.0
    ) -> Dict:
        try:
            return cart_totals(cart, discount, tax_rate)
        except Exception as e:
            logger.error("Error calculating totals: %s", e)
            return {"subtotal": 0, "discount": 0, "tax": 0, "total": 0}

    def checkout(
        self,
        cart: List[Dict],
        payment_method: str,
        amount_paid: float,
        discount: float = 0.0,
        tax_rate: float = 0.0,
        customer_id: int = None,
    ) -> Tuple[bool, Optional[int], float, str]:
        if self.auth_service and not self.auth_service.user_has_permission(
            "process_sale"
        ):
            return False, None, 0, "Insufficient permissions to process sales"

        try:
            user_id = (
                self.auth_service.get_current_user().get("user_id")
                if self.auth_service
                else None
            )
            return process_sale(
                cart,
                user_id,
                payment_method,
                amount_paid,
                discount,
                tax_rate,
                customer_id,
            )
        except Exception as e:
            logger.error("Checkout error: %s", e)
            return False, None, 0, f"Error: {str(e)}"

    def get_receipt(self, sale_id: int, store_name: str = "POS System") -> str:
        try:
            return generate_receipt(sale_id, store_name)
        except Exception as e:
            logger.error("Receipt error: %s", e)
            return f"Error generating receipt: {str(e)}"

    def get_cart_summary(self, cart: List[Dict]) -> Dict:
        try:
            item_count = get_cart_item_count(cart)
            totals = cart_totals(cart)
            return {
                "item_count": item_count,
                "total_value": totals.get("total", 0),
                "item_lines": len(cart),
            }
        except Exception as e:
            logger.error("Error getting cart summary: %s", e)
            return {"item_count": 0, "total_value": 0, "item_lines": 0}
