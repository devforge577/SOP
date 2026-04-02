"""
Product Service

Handles product management operations.
Coordinates between presentation layer and product module.
"""

from typing import List, Dict, Optional, Tuple
from modules.products import (
    ProductManager,
    get_all_products, search_products, get_product_by_barcode,
    get_product_by_id, add_product, update_product, delete_product,
    get_categories, get_low_stock_products
)
import logging

logger = logging.getLogger(__name__)


class ProductService:
    """Service layer for product operations."""

    def __init__(self, auth_service=None):
        self.product_manager = ProductManager()
        self.auth_service = auth_service

    def get_all_products(self, include_inactive: bool = False) -> List[Dict]:
        """
        Retrieve all products.
        
        Args:
            include_inactive: Include inactive/deleted products
            
        Returns:
            List of product dictionaries
        """
        try:
            return get_all_products(include_inactive)
        except Exception as e:
            logger.error(f"Error retrieving products: {e}")
            return []

    def search_products(self, keyword: str) -> List[Dict]:
        """
        Search products by name, category, or barcode.
        
        Args:
            keyword: Search term
            
        Returns:
            List of matching products
        """
        try:
            return search_products(keyword)
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def get_product_by_barcode(self, barcode: str) -> Optional[Dict]:
        """
        Get single product by barcode (for POS scanning).
        
        Args:
            barcode: Product barcode
            
        Returns:
            Product dictionary or None
        """
        try:
            return get_product_by_barcode(barcode)
        except Exception as e:
            logger.error(f"Barcode lookup error: {e}")
            return None

    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """
        Get single product by ID.
        
        Args:
            product_id: Product identifier
            
        Returns:
            Product dictionary or None
        """
        try:
            return get_product_by_id(product_id)
        except Exception as e:
            logger.error(f"Product lookup error: {e}")
            return None

    def get_categories(self) -> List[str]:
        """Get all product categories."""
        try:
            return get_categories()
        except Exception as e:
            logger.error(f"Error retrieving categories: {e}")
            return []

    def get_low_stock_products(self) -> List[Dict]:
        """Get products below low stock threshold."""
        try:
            return get_low_stock_products()
        except Exception as e:
            logger.error(f"Error retrieving low stock: {e}")
            return []

    def add_product(self, product_name: str, category: str, price: float,
                    barcode: str = None, supplier: str = None,
                    initial_stock: int = 0, low_stock_alert: int = 5) -> Tuple[bool, str]:
        """
        Add new product (requires manager/admin role).
        
        Args:
            product_name: Name of product
            category: Product category
            price: Unit price
            barcode: Optional barcode
            supplier: Optional supplier name
            initial_stock: Starting inventory level
            low_stock_alert: Alert threshold
            
        Returns:
            (success: bool, message: str)
        """
        if self.auth_service and not self.auth_service.user_has_permission('manage_products'):
            return False, "Insufficient permissions to add products"
        
        try:
            user_id = self.auth_service.get_current_user().get('user_id') if self.auth_service else None
            return add_product(product_name, category, price, barcode, supplier,
                             initial_stock, low_stock_alert, user_id)
        except Exception as e:
            logger.error(f"Error adding product: {e}")
            return False, f"Error: {str(e)}"

    def update_product(self, product_id: int, **kwargs) -> Tuple[bool, str]:
        """
        Update product details (requires manager/admin role).
        
        Args:
            product_id: Product to update
            **kwargs: Fields to update (product_name, category, price, etc.)
            
        Returns:
            (success: bool, message: str)
        """
        if self.auth_service and not self.auth_service.user_has_permission('manage_products'):
            return False, "Insufficient permissions to update products"
        
        try:
            user_id = self.auth_service.get_current_user().get('user_id') if self.auth_service else None
            return update_product(product_id, user_id=user_id, **kwargs)
        except Exception as e:
            logger.error(f"Error updating product: {e}")
            return False, f"Error: {str(e)}"

    def delete_product(self, product_id: int) -> Tuple[bool, str]:
        """
        Delete/deactivate product (requires manager/admin role).
        
        Args:
            product_id: Product to delete
            
        Returns:
            (success: bool, message: str)
        """
        if self.auth_service and not self.auth_service.user_has_permission('manage_products'):
            return False, "Insufficient permissions to delete products"
        
        try:
            return delete_product(product_id)
        except Exception as e:
            logger.error(f"Error deleting product: {e}")
            return False, f"Error: {str(e)}"
