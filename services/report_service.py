"""
Report Service

Handles reporting and analytics operations.
Coordinates between presentation layer and reports module.
"""

from typing import List, Dict
from modules.reports import (
    get_daily_summary,
    get_sales_by_date_range,
    get_top_products,
    get_payment_method_breakdown,
    get_cashier_performance,
    get_inventory_report,
    get_recent_transactions,
    get_low_performing_products,
)
import logging

logger = logging.getLogger(__name__)


class ReportService:
    """Service layer for reporting operations."""

    def __init__(self, auth_service=None):
        self.auth_service = auth_service

    def get_daily_summary(self, date: str = None) -> Dict:
        """
        Get summary for a specific date.

        Args:
            date: Date in YYYY-MM-DD format, defaults to today

        Returns:
            Dictionary with daily totals and metrics
        """
        if self.auth_service and not self.auth_service.user_has_permission(
            "view_reports"
        ):
            return {}

        try:
            return get_daily_summary(date)
        except Exception as e:
            logger.error(f"Error getting daily summary: {e}")
            return {}

    def get_sales_range(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Get sales summary for date range.

        Args:
            start_date: Start date YYYY-MM-DD
            end_date: End date YYYY-MM-DD

        Returns:
            List of daily sales summaries
        """
        if self.auth_service and not self.auth_service.user_has_permission(
            "view_reports"
        ):
            return []

        try:
            return get_sales_by_date_range(start_date, end_date)
        except Exception as e:
            logger.error(f"Error getting sales range: {e}")
            return []

    def get_top_products(
        self, limit: int = 10, start_date: str = None, end_date: str = None
    ) -> List[Dict]:
        """
        Get best-selling products.

        Args:
            limit: Number of products to return
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of top products with sales metrics
        """
        if self.auth_service and not self.auth_service.user_has_permission(
            "view_reports"
        ):
            return []

        try:
            return get_top_products(limit, start_date, end_date)
        except Exception as e:
            logger.error(f"Error getting top products: {e}")
            return []

    def get_payment_breakdown(
        self, start_date: str = None, end_date: str = None
    ) -> List[Dict]:
        """
        Get revenue breakdown by payment method.

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of payment method summaries
        """
        if self.auth_service and not self.auth_service.user_has_permission(
            "view_reports"
        ):
            return []

        try:
            return get_payment_method_breakdown(start_date, end_date)
        except Exception as e:
            logger.error(f"Error getting payment breakdown: {e}")
            return []

    def get_cashier_performance(
        self, start_date: str = None, end_date: str = None
    ) -> List[Dict]:
        """
        Get performance metrics per cashier.

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of cashier performance records
        """
        if self.auth_service and not self.auth_service.user_has_permission(
            "view_reports"
        ):
            return []

        try:
            return get_cashier_performance(start_date, end_date)
        except Exception as e:
            logger.error(f"Error getting cashier performance: {e}")
            return []

    def get_inventory_status(self) -> List[Dict]:
        """
        Get current inventory levels and status.

        Returns:
            List of inventory items
        """
        if self.auth_service and not self.auth_service.user_has_permission(
            "view_reports"
        ):
            return []

        try:
            return get_inventory_report()
        except Exception as e:
            logger.error(f"Error getting inventory: {e}")
            return []

    def get_low_stock_alert(self) -> List[Dict]:
        """Get products below low stock threshold."""
        try:
            return get_low_performing_products(limit=20, days=30)
        except Exception as e:
            logger.error(f"Error getting low stock: {e}")
            return []

    def get_recent_activity(self, limit: int = 20) -> List[Dict]:
        """Get recent transaction activity."""
        if self.auth_service and not self.auth_service.user_has_permission(
            "view_reports"
        ):
            return []

        try:
            return get_recent_transactions(limit)
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return []
