"""
Payment Service Layer

Coordinates payment processing with permission checking and error handling.
Provides high-level API for views and application logic.
"""

import logging
from typing import Tuple, Optional, Dict, List, Any
from modules.payments import (
    process_payment,
    get_payment_summary,
    get_pending_payments,
    reconcile_payments,
    get_cash_drawer_summary,
    process_refund,
    PaymentMethod,
    PaymentStatus
)
from modules.auth import has_permission

logger = logging.getLogger(__name__)


class PaymentService:
    """
    High-level payment service with permission checking and error handling.
    """
    
    # Required permission for payment operations
    CASHIER_PERMISSION = 'process_sales'
    MANAGER_PERMISSION = 'manage_payments'
    
    @staticmethod
    def checkout_payment(user_id: int, amount_paid: float, total_amount: float, 
                        sale_id: int, payment_method: str, **kwargs) -> Tuple[bool, Optional[str], str]:
        """
        Process payment at checkout (cashier operation).
        
        Args:
            user_id: User ID of cashier
            amount_paid: Amount tendered
            total_amount: Sale total
            sale_id: Sale ID
            payment_method: Payment method
            **kwargs: Payment-specific parameters
            
        Returns:
            (success, transaction_id, message)
        """
        try:
            # Check permission
            if not has_permission(user_id, PaymentService.CASHIER_PERMISSION):
                msg = "Permission denied: You do not have permission to process payments"
                logger.warning(f"[PAYMENT] Unauthorized payment attempt by user {user_id}")
                return False, None, msg
            
            # Process payment
            success, transaction_id, msg = process_payment(
                amount_paid=amount_paid,
                total_amount=total_amount,
                sale_id=sale_id,
                payment_method=payment_method,
                **kwargs
            )
            
            if success:
                logger.info(f"[PAYMENT SERVICE] User {user_id} processed payment for sale {sale_id} "
                           f"(GHS {amount_paid:.2f}) via {payment_method}")
            else:
                logger.warning(f"[PAYMENT SERVICE] Payment failed for sale {sale_id}: {msg}")
            
            return success, transaction_id, msg
            
        except Exception as e:
            logger.error(f"[PAYMENT SERVICE] Error in checkout_payment: {str(e)}")
            return False, None, f"Payment service error: {str(e)}"
    
    @staticmethod
    def get_payment_report(user_id: int, start_date: str = None, 
                          end_date: str = None) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Get payment summary report (manager operation).
        
        Args:
            user_id: User ID requesting report
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            (success, report_dict)
        """
        try:
            # Check permission
            if not has_permission(user_id, PaymentService.MANAGER_PERMISSION):
                msg = "Permission denied: You do not have permission to view payment reports"
                logger.warning(f"[PAYMENT] Unauthorized report request by user {user_id}")
                return False, None
            
            # Get summary
            summary = get_payment_summary(start_date, end_date)
            
            if 'error' in summary:
                return False, None
            
            logger.info(f"[PAYMENT SERVICE] User {user_id} generated payment report for "
                       f"{summary['period']}")
            return True, summary
            
        except Exception as e:
            logger.error(f"[PAYMENT SERVICE] Error generating payment report: {str(e)}")
            return False, None
    
    @staticmethod
    def get_pending_transactions(user_id: int) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Get pending payment transactions (manager operation).
        
        Args:
            user_id: User ID requesting list
            
        Returns:
            (success, pending_payments_list)
        """
        try:
            # Check permission
            if not has_permission(user_id, PaymentService.MANAGER_PERMISSION):
                msg = "Permission denied: You do not have permission to view pending payments"
                logger.warning(f"[PAYMENT] Unauthorized pending request by user {user_id}")
                return False, []
            
            pending = get_pending_payments()
            logger.info(f"[PAYMENT SERVICE] User {user_id} viewed {len(pending)} pending payments")
            return True, pending
            
        except Exception as e:
            logger.error(f"[PAYMENT SERVICE] Error getting pending payments: {str(e)}")
            return False, []
    
    @staticmethod
    def reconcile_day(user_id: int, date: str = None) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Reconcile payments for a date (manager operation).
        
        Args:
            user_id: User ID performing reconciliation
            date: Date to reconcile (YYYY-MM-DD)
            
        Returns:
            (success, reconciliation_report)
        """
        try:
            # Check permission
            if not has_permission(user_id, PaymentService.MANAGER_PERMISSION):
                msg = "Permission denied: You do not have permission to reconcile payments"
                logger.warning(f"[PAYMENT] Unauthorized reconciliation attempt by user {user_id}")
                return False, None
            
            success, report = reconcile_payments(date)
            
            if success:
                logger.info(f"[PAYMENT SERVICE] User {user_id} reconciled payments for {date}")
            
            return success, report
            
        except Exception as e:
            logger.error(f"[PAYMENT SERVICE] Error reconciling payments: {str(e)}")
            return False, None
    
    @staticmethod
    def get_cash_drawer(user_id: int, date: str = None) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Get cash drawer summary (manager operation).
        
        Args:
            user_id: User ID requesting summary
            date: Date to summarize (YYYY-MM-DD)
            
        Returns:
            (success, drawer_summary)
        """
        try:
            # Check permission
            if not has_permission(user_id, PaymentService.MANAGER_PERMISSION):
                msg = "Permission denied: You do not have permission to view cash drawer"
                logger.warning(f"[PAYMENT] Unauthorized drawer request by user {user_id}")
                return False, None
            
            drawer = get_cash_drawer_summary(date)
            
            if 'error' in drawer:
                return False, None
            
            logger.info(f"[PAYMENT SERVICE] User {user_id} viewed cash drawer for {date}")
            return True, drawer
            
        except Exception as e:
            logger.error(f"[PAYMENT SERVICE] Error getting cash drawer: {str(e)}")
            return False, None
    
    @staticmethod
    def process_refund_request(user_id: int, payment_id: int, reason: str, 
                              refund_amount: float = None) -> Tuple[bool, str]:
        """
        Process a refund request (manager operation).
        
        Args:
            user_id: User ID processing refund
            payment_id: Payment ID to refund
            reason: Refund reason
            refund_amount: Partial refund amount (None = full)
            
        Returns:
            (success, message)
        """
        try:
            # Check permission
            if not has_permission(user_id, PaymentService.MANAGER_PERMISSION):
                msg = "Permission denied: You do not have permission to process refunds"
                logger.warning(f"[PAYMENT] Unauthorized refund attempt by user {user_id}")
                return False, msg
            
            success, msg = process_refund(payment_id, reason, refund_amount)
            
            if success:
                logger.info(f"[PAYMENT SERVICE] User {user_id} processed refund for payment {payment_id}")
            
            return success, msg
            
        except Exception as e:
            logger.error(f"[PAYMENT SERVICE] Error processing refund: {str(e)}")
            return False, f"Refund service error: {str(e)}"


# ══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS FOR COMMON OPERATIONS
# ══════════════════════════════════════════════════════════════════════════════

def process_cash_checkout(user_id: int, amount_paid: float, total_amount: float, 
                         sale_id: int) -> Tuple[bool, Optional[str], float, str]:
    """
    Quick cash checkout function.
    
    Returns:
        (success, transaction_id, change, message)
    """
    success, txn_id, msg = PaymentService.checkout_payment(
        user_id=user_id,
        amount_paid=amount_paid,
        total_amount=total_amount,
        sale_id=sale_id,
        payment_method='cash'
    )
    
    change = amount_paid - total_amount if success else 0
    return success, txn_id, change, msg


def process_momo_checkout(user_id: int, amount_paid: float, total_amount: float, 
                         sale_id: int, phone_number: str, reference: str) -> Tuple[bool, Optional[str], str]:
    """
    Quick MoMo checkout function.
    
    Returns:
        (success, transaction_id, message)
    """
    return PaymentService.checkout_payment(
        user_id=user_id,
        amount_paid=amount_paid,
        total_amount=total_amount,
        sale_id=sale_id,
        payment_method='momo',
        phone_number=phone_number,
        reference=reference
    )


def process_card_checkout(user_id: int, amount_paid: float, total_amount: float,
                         sale_id: int, card_number: str, expiry: str, cvv: str,
                         cardholder_name: str) -> Tuple[bool, Optional[str], str]:
    """
    Quick card checkout function.
    
    Returns:
        (success, transaction_id, message)
    """
    return PaymentService.checkout_payment(
        user_id=user_id,
        amount_paid=amount_paid,
        total_amount=total_amount,
        sale_id=sale_id,
        payment_method='card',
        card_number=card_number,
        expiry=expiry,
        cvv=cvv,
        cardholder_name=cardholder_name
    )
