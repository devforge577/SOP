"""
Payment Processing Module

Handles all payment operations including:
- Multiple payment methods (Cash, MoMo, Card, Bank Transfer)
- Payment validation and verification
- Payment gateway integration
- Payment reconciliation
- Transaction logging

Author: POS System
Date: 2026
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Tuple, Optional, Dict, List, Any
from enum import Enum
from database.db import get_db_connection

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# ENUMS & CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

class PaymentMethod(Enum):
    """Supported payment methods"""
    CASH = "cash"
    MOMO = "momo"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"


class PaymentStatus(Enum):
    """Payment processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"


class TransactionType(Enum):
    """Transaction types for reconciliation"""
    SALE = "sale"
    REFUND = "refund"
    VOID = "void"
    CHARGE = "charge"
    REVERSAL = "reversal"


# Default transaction fees (in percentage)
PAYMENT_FEES = {
    PaymentMethod.CASH.value: 0.0,
    PaymentMethod.MOMO.value: 1.5,           # 1.5% MoMo fee
    PaymentMethod.CARD.value: 2.5,           # 2.5% Card processing fee
    PaymentMethod.BANK_TRANSFER.value: 0.0,  # No fee for bank transfers
}

# Payment gateway credentials (should be in environment variables in production)
PAYMENT_GATEWAY_CONFIG = {
    'stripe': {
        'api_key': None,  # Set from environment
        'webhook_secret': None,
    },
    'paystack': {
        'secret_key': None,  # Set from environment
        'public_key': None,
    },
    'momo': {
        'api_key': None,  # Set from environment
        'api_user': None,
    }
}


# ══════════════════════════════════════════════════════════════════════════════
# PAYMENT VALIDATORS
# ══════════════════════════════════════════════════════════════════════════════

def validate_payment_method(method: str) -> Tuple[bool, str]:
    """
    Validate if payment method is supported.
    
    Args:
        method: Payment method string
        
    Returns:
        (is_valid, error_message)
    """
    valid_methods = [pm.value for pm in PaymentMethod]
    if method.lower() not in valid_methods:
        return False, f"Unsupported payment method: {method}. Supported: {', '.join(valid_methods)}"
    return True, ""


def validate_amount(amount: float) -> Tuple[bool, str]:
    """
    Validate payment amount.
    
    Args:
        amount: Payment amount
        
    Returns:
        (is_valid, error_message)
    """
    try:
        amt = Decimal(str(amount))
        if amt <= 0:
            return False, "Amount must be greater than 0"
        if amt > 999999.99:
            return False, "Amount exceeds maximum limit (999,999.99)"
        return True, ""
    except Exception as e:
        return False, f"Invalid amount format: {str(e)}"


def validate_cash_payment(amount_paid: float, total_amount: float) -> Tuple[bool, str]:
    """
    Validate cash payment (amount must be >= total).
    
    Args:
        amount_paid: Cash tendered
        total_amount: Sale total
        
    Returns:
        (is_valid, error_message)
    """
    if amount_paid < total_amount:
        change_needed = total_amount - amount_paid
        return False, f"Insufficient payment. Need additional GHS {change_needed:.2f}"
    return True, ""


def validate_card_payment(card_number: str, expiry: str, cvv: str) -> Tuple[bool, str]:
    """
    Validate card payment details (basic validation, not actual processing).
    
    Args:
        card_number: Card number (16 digits)
        expiry: Expiry date (MM/YY)
        cvv: CVV (3-4 digits)
        
    Returns:
        (is_valid, error_message)
    """
    # Basic validation - in production use proper library like luhn algorithm
    card_number = card_number.replace(" ", "").replace("-", "")
    
    if len(card_number) not in [13, 14, 15, 16]:
        return False, "Invalid card number length"
    
    if not card_number.isdigit():
        return False, "Card number must contain only digits"
    
    if not expiry or len(expiry.split('/')) != 2:
        return False, "Invalid expiry format (use MM/YY)"
    
    if not cvv or len(cvv) not in [3, 4]:
        return False, "CVV must be 3-4 digits"
    
    return True, ""


def validate_reference(reference: str) -> Tuple[bool, str]:
    """
    Validate transaction reference for MoMo or bank transfer.
    
    Args:
        reference: Transaction reference number
        
    Returns:
        (is_valid, error_message)
    """
    if not reference or len(reference.strip()) == 0:
        return False, "Reference number is required"
    if len(reference) > 50:
        return False, "Reference number too long (max 50 characters)"
    return True, ""


# ══════════════════════════════════════════════════════════════════════════════
# PAYMENT PROCESSORS
# ══════════════════════════════════════════════════════════════════════════════

def process_cash_payment(amount_paid: float, total_amount: float, sale_id: int) -> Tuple[bool, float, str]:
    """
    Process cash payment.
    
    Args:
        amount_paid: Cash tendered
        total_amount: Sale total
        sale_id: Sale ID for reference
        
    Returns:
        (success, change, message)
    """
    try:
        # Validate
        valid, msg = validate_cash_payment(amount_paid, total_amount)
        if not valid:
            logger.warning(f"[CASH] Validation failed for sale {sale_id}: {msg}")
            return False, 0, msg
        
        # Calculate change
        change = float(amount_paid) - float(total_amount)
        
        # Log transaction
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO payments (sale_id, amount_paid, change_given, payment_method, status)
                VALUES (?, ?, ?, ?, ?)
            """, (sale_id, amount_paid, change, PaymentMethod.CASH.value, PaymentStatus.COMPLETED.value))
        
        logger.info(f"[CASH] Payment processed: Sale {sale_id}, Amount: GHS {amount_paid:.2f}, Change: GHS {change:.2f}")
        return True, change, f"Cash payment accepted. Change: GHS {change:.2f}"
        
    except Exception as e:
        logger.error(f"[CASH] Error processing payment for sale {sale_id}: {str(e)}")
        return False, 0, f"Error processing cash payment: {str(e)}"


def process_momo_payment(amount_paid: float, total_amount: float, sale_id: int, 
                         phone_number: str, reference: str, provider: str = "mtn") -> Tuple[bool, str, str]:
    """
    Process Mobile Money (MoMo) payment.
    
    Args:
        amount_paid: Payment amount
        total_amount: Sale total
        sale_id: Sale ID
        phone_number: Customer phone number
        reference: MoMo transaction reference
        provider: Provider ('mtn' or 'vodafone')
        
    Returns:
        (success, transaction_id, message)
    """
    try:
        # Validate inputs
        valid, msg = validate_amount(amount_paid)
        if not valid:
            return False, "", msg
        
        valid, msg = validate_reference(reference)
        if not valid:
            return False, "", msg
        
        # In production, call MoMo API here
        # For now, simulate successful transaction
        transaction_id = f"MOM-{sale_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Calculate fee
        fee_percentage = PAYMENT_FEES[PaymentMethod.MOMO.value]
        fee = float(amount_paid) * (fee_percentage / 100)
        net_amount = float(amount_paid) - fee
        
        # Validate amount
        if net_amount < float(total_amount):
            return False, "", f"Amount after fee (GHS {net_amount:.2f}) is insufficient. Need GHS {total_amount:.2f}"
        
        # Log transaction
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO payments 
                (sale_id, amount_paid, change_given, payment_method, status, reference, provider, fee)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (sale_id, amount_paid, 0, PaymentMethod.MOMO.value, PaymentStatus.COMPLETED.value, 
                  reference, provider, fee))
        
        logger.info(f"[MOMO] Payment processed: Sale {sale_id}, Amount: GHS {amount_paid:.2f}, "
                   f"Fee: GHS {fee:.2f}, Reference: {reference}")
        
        return True, transaction_id, f"MoMo payment confirmed. Transaction ID: {transaction_id}"
        
    except Exception as e:
        logger.error(f"[MOMO] Error processing payment for sale {sale_id}: {str(e)}")
        return False, "", f"Error processing MoMo payment: {str(e)}"


def process_card_payment(amount_paid: float, total_amount: float, sale_id: int,
                        card_number: str, expiry: str, cvv: str, 
                        cardholder_name: str) -> Tuple[bool, str, str]:
    """
    Process card payment (with gateway integration).
    
    Args:
        amount_paid: Payment amount
        total_amount: Sale total
        sale_id: Sale ID
        card_number: Card number
        expiry: Expiry date (MM/YY)
        cvv: CVV
        cardholder_name: Name on card
        
    Returns:
        (success, transaction_id, message)
    """
    try:
        # Validate inputs
        valid, msg = validate_amount(amount_paid)
        if not valid:
            return False, "", msg
        
        valid, msg = validate_card_payment(card_number, expiry, cvv)
        if not valid:
            return False, "", msg
        
        # Calculate fee
        fee_percentage = PAYMENT_FEES[PaymentMethod.CARD.value]
        fee = float(amount_paid) * (fee_percentage / 100)
        net_amount = float(amount_paid) - fee
        
        # Validate amount
        if net_amount < float(total_amount):
            return False, "", f"Amount after fee (GHS {net_amount:.2f}) is insufficient. Need GHS {total_amount:.2f}"
        
        # Process with gateway (Paystack, Stripe, etc.)
        # For now, simulate successful transaction
        gateway_response = _call_payment_gateway(
            method='card',
            amount=float(amount_paid),
            card_number=card_number[-4:],  # Only last 4 digits for logging
            cardholder=cardholder_name
        )
        
        if not gateway_response['success']:
            logger.warning(f"[CARD] Gateway declined: {gateway_response['message']}")
            return False, "", f"Card declined: {gateway_response['message']}"
        
        transaction_id = gateway_response['transaction_id']
        
        # Log transaction
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO payments 
                (sale_id, amount_paid, change_given, payment_method, status, reference, fee)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (sale_id, amount_paid, 0, PaymentMethod.CARD.value, PaymentStatus.COMPLETED.value,
                  transaction_id, fee))
        
        logger.info(f"[CARD] Payment processed: Sale {sale_id}, Amount: GHS {amount_paid:.2f}, "
                   f"Fee: GHS {fee:.2f}, Card: ****{card_number[-4:]}")
        
        return True, transaction_id, f"Card payment approved. Reference: {transaction_id}"
        
    except Exception as e:
        logger.error(f"[CARD] Error processing payment for sale {sale_id}: {str(e)}")
        return False, "", f"Error processing card payment: {str(e)}"


def process_bank_transfer(amount_paid: float, total_amount: float, sale_id: int,
                         account_holder: str, reference: str) -> Tuple[bool, str, str]:
    """
    Process bank transfer payment.
    
    Args:
        amount_paid: Payment amount
        total_amount: Sale total
        sale_id: Sale ID
        account_holder: Name of account holder
        reference: Bank transaction reference
        
    Returns:
        (success, transaction_id, message)
    """
    try:
        # Validate inputs
        valid, msg = validate_amount(amount_paid)
        if not valid:
            return False, "", msg
        
        valid, msg = validate_reference(reference)
        if not valid:
            return False, "", msg
        
        # Bank transfers are typically verified later
        transaction_id = f"BANK-{sale_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Log as PENDING until bank verifies
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO payments 
                (sale_id, amount_paid, change_given, payment_method, status, reference)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sale_id, amount_paid, 0, PaymentMethod.BANK_TRANSFER.value, 
                  PaymentStatus.PENDING.value, reference))
        
        logger.info(f"[BANK] Payment initiated: Sale {sale_id}, Amount: GHS {amount_paid:.2f}, "
                   f"Reference: {reference} [PENDING VERIFICATION]")
        
        return True, transaction_id, f"Bank transfer initiated. Reference: {reference}. Awaiting verification."
        
    except Exception as e:
        logger.error(f"[BANK] Error processing payment for sale {sale_id}: {str(e)}")
        return False, "", f"Error processing bank transfer: {str(e)}"


# ══════════════════════════════════════════════════════════════════════════════
# PAYMENT GATEWAY INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════

def _call_payment_gateway(method: str, amount: float, **kwargs) -> Dict[str, Any]:
    """
    Call external payment gateway (Paystack, Stripe, etc.)
    
    This is a placeholder - implement actual gateway calls in production.
    
    Args:
        method: Payment method ('card', 'momo', etc.)
        amount: Payment amount
        **kwargs: Additional parameters
        
    Returns:
        Gateway response dict with 'success', 'transaction_id', 'message'
    """
    # TODO: Implement actual gateway integration
    # Examples:
    # - Paystack: https://paystack.com/docs/api/
    # - Stripe: https://stripe.com/docs/api
    # - MTN MoMo: https://momoapi.mtn.com/
    
    # For now, simulate successful response
    if method == 'card':
        return {
            'success': True,
            'transaction_id': f"CARD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'message': 'Card payment processed successfully'
        }
    
    return {
        'success': False,
        'transaction_id': None,
        'message': 'Payment gateway not configured'
    }


def verify_payment_with_gateway(payment_id: int) -> Tuple[bool, str]:
    """
    Verify payment status with payment gateway.
    
    Args:
        payment_id: Payment record ID
        
    Returns:
        (is_verified, message)
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,))
            payment = cursor.fetchone()
            
            if not payment:
                return False, "Payment not found"
            
            # TODO: Call gateway API to verify
            # Update payment status based on gateway response
            
            return True, "Payment verified"
            
    except Exception as e:
        logger.error(f"Error verifying payment {payment_id}: {str(e)}")
        return False, f"Error verifying payment: {str(e)}"


# ══════════════════════════════════════════════════════════════════════════════
# PAYMENT RECONCILIATION & REPORTING
# ══════════════════════════════════════════════════════════════════════════════

def get_payment_summary(start_date: str = None, end_date: str = None) -> Dict[str, Any]:
    """
    Get payment summary for a date range.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        
    Returns:
        Summary dict with totals by payment method
    """
    try:
        if not start_date:
            start_date = datetime.now().strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Total by method
            cursor.execute("""
                SELECT 
                    payment_method,
                    COUNT(*) as transactions,
                    SUM(amount_paid) as total_amount,
                    SUM(fee) as total_fees,
                    SUM(amount_paid - COALESCE(fee, 0)) as net_amount,
                    AVG(amount_paid) as avg_amount
                FROM payments
                WHERE DATE(payment_date) BETWEEN ? AND ? AND status = ?
                GROUP BY payment_method
            """, (start_date, end_date, PaymentStatus.COMPLETED.value))
            
            methods = cursor.fetchall()
            summary = {
                'period': f"{start_date} to {end_date}",
                'total_transactions': 0,
                'total_revenue': 0.0,
                'total_fees': 0.0,
                'net_revenue': 0.0,
                'by_method': {}
            }
            
            for method in methods:
                summary['by_method'][method['payment_method']] = {
                    'transactions': method['transactions'],
                    'total_amount': method['total_amount'] or 0.0,
                    'fees': method['total_fees'] or 0.0,
                    'net_amount': method['net_amount'] or 0.0,
                    'avg_amount': float(method['avg_amount']) if method['avg_amount'] else 0.0
                }
                summary['total_transactions'] += method['transactions']
                summary['total_revenue'] += method['total_amount'] or 0.0
                summary['total_fees'] += method['total_fees'] or 0.0
                summary['net_revenue'] += method['net_amount'] or 0.0
            
            return summary
            
    except Exception as e:
        logger.error(f"Error getting payment summary: {str(e)}")
        return {'error': str(e)}


def get_pending_payments() -> List[Dict[str, Any]]:
    """
    Get all pending payments awaiting verification.
    
    Returns:
        List of pending payments
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    p.payment_id,
                    p.sale_id,
                    p.amount_paid,
                    p.payment_method,
                    p.reference,
                    p.payment_date,
                    s.total_amount
                FROM payments p
                JOIN sales s ON p.sale_id = s.sale_id
                WHERE p.status = ?
                ORDER BY p.payment_date DESC
            """, (PaymentStatus.PENDING.value,))
            
            return [dict(row) for row in cursor.fetchall()]
            
    except Exception as e:
        logger.error(f"Error getting pending payments: {str(e)}")
        return []


def reconcile_payments(date: str = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Reconcile payments for a given date.
    
    Args:
        date: Date to reconcile (YYYY-MM-DD)
        
    Returns:
        (success, reconciliation_report)
    """
    try:
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get all transactions for the date
            cursor.execute("""
                SELECT 
                    p.payment_method,
                    p.status,
                    COUNT(*) as transactions,
                    SUM(p.amount_paid) as total_amount,
                    SUM(p.fee) as total_fees
                FROM payments p
                WHERE DATE(p.payment_date) = ?
                GROUP BY p.payment_method, p.status
            """, (date,))
            
            transactions = cursor.fetchall()
            
            report = {
                'reconciliation_date': date,
                'timestamp': datetime.now().isoformat(),
                'status': 'COMPLETE',
                'transactions': [],
                'totals': {
                    'completed': 0.0,
                    'pending': 0.0,
                    'failed': 0.0,
                    'total': 0.0
                }
            }
            
            for txn in transactions:
                record = {
                    'method': txn['payment_method'],
                    'status': txn['status'],
                    'count': txn['transactions'],
                    'amount': txn['total_amount'] or 0.0,
                    'fees': txn['total_fees'] or 0.0
                }
                report['transactions'].append(record)
                
                if txn['status'] == PaymentStatus.COMPLETED.value:
                    report['totals']['completed'] += record['amount']
                elif txn['status'] == PaymentStatus.PENDING.value:
                    report['totals']['pending'] += record['amount']
                elif txn['status'] == PaymentStatus.FAILED.value:
                    report['totals']['failed'] += record['amount']
            
            report['totals']['total'] = (report['totals']['completed'] + 
                                        report['totals']['pending'] + 
                                        report['totals']['failed'])
            
            logger.info(f"[RECONCILIATION] {date}: Completed: GHS {report['totals']['completed']:.2f}, "
                       f"Pending: GHS {report['totals']['pending']:.2f}")
            
            return True, report
            
    except Exception as e:
        logger.error(f"Error reconciling payments: {str(e)}")
        return False, {'error': str(e)}


def get_cash_drawer_summary(date: str = None) -> Dict[str, Any]:
    """
    Get cash drawer summary (cash payments only).
    
    Args:
        date: Date to summarize (YYYY-MM-DD)
        
    Returns:
        Cash drawer summary with opening, transactions, closing
    """
    try:
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get all cash transactions
            cursor.execute("""
                SELECT 
                    SUM(p.amount_paid) as total_received,
                    SUM(p.change_given) as total_change,
                    COUNT(*) as transactions
                FROM payments p
                WHERE DATE(p.payment_date) = ? AND p.payment_method = ? AND p.status = ?
            """, (date, PaymentMethod.CASH.value, PaymentStatus.COMPLETED.value))
            
            result = cursor.fetchone()
            
            total_received = result['total_received'] or 0.0
            total_change = result['total_change'] or 0.0
            transactions = result['transactions'] or 0
            net_cash = total_received - total_change
            
            return {
                'date': date,
                'transactions': transactions,
                'total_received': total_received,
                'total_change': total_change,
                'net_cash': net_cash,
                'currency': 'GHS'
            }
            
    except Exception as e:
        logger.error(f"Error getting cash drawer summary: {str(e)}")
        return {'error': str(e)}


# ══════════════════════════════════════════════════════════════════════════════
# REFUND & REVERSAL OPERATIONS
# ══════════════════════════════════════════════════════════════════════════════

def process_refund(payment_id: int, reason: str, refund_amount: float = None) -> Tuple[bool, str]:
    """
    Process a payment refund.
    
    Args:
        payment_id: Payment ID to refund
        reason: Refund reason
        refund_amount: Partial refund amount (None = full refund)
        
    Returns:
        (success, message)
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get original payment
            cursor.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,))
            payment = cursor.fetchone()
            
            if not payment:
                return False, "Payment not found"
            
            if payment['status'] != PaymentStatus.COMPLETED.value:
                return False, f"Cannot refund {payment['status']} payment"
            
            # Calculate refund amount
            original_amount = payment['amount_paid']
            if refund_amount is None:
                refund_amount = original_amount
            elif refund_amount > original_amount:
                return False, f"Refund amount (GHS {refund_amount:.2f}) exceeds original amount (GHS {original_amount:.2f})"
            
            # Create refund record
            cursor.execute("""
                INSERT INTO payments (sale_id, amount_paid, payment_method, status, reference)
                VALUES (?, ?, ?, ?, ?)
            """, (payment['sale_id'], -refund_amount, payment['payment_method'], 
                  PaymentStatus.COMPLETED.value, f"REFUND-{payment_id}"))
            
            logger.info(f"[REFUND] Refunded GHS {refund_amount:.2f} for payment {payment_id}. Reason: {reason}")
            
            return True, f"Refund of GHS {refund_amount:.2f} processed. Reference: REFUND-{payment_id}"
            
    except Exception as e:
        logger.error(f"Error processing refund: {str(e)}")
        return False, f"Error processing refund: {str(e)}"


# ══════════════════════════════════════════════════════════════════════════════
# ROUTER FUNCTION - MAIN PAYMENT ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def process_payment(amount_paid: float, total_amount: float, sale_id: int,
                   payment_method: str, **kwargs) -> Tuple[bool, Optional[str], str]:
    """
    Main payment processing function - routes to appropriate payment method handler.
    
    Args:
        amount_paid: Amount paid by customer
        total_amount: Total sale amount
        sale_id: Sale ID
        payment_method: Payment method (cash, momo, card, bank_transfer)
        **kwargs: Method-specific parameters
            - cash: (none required)
            - momo: phone_number, reference, provider
            - card: card_number, expiry, cvv, cardholder_name
            - bank_transfer: account_holder, reference
        
    Returns:
        (success, transaction_id, message)
    """
    try:
        # Validate payment method
        valid, msg = validate_payment_method(payment_method)
        if not valid:
            logger.error(f"Invalid payment method: {payment_method}")
            return False, None, msg
        
        # Route to appropriate handler
        if payment_method.lower() == PaymentMethod.CASH.value:
            success, change, msg = process_cash_payment(amount_paid, total_amount, sale_id)
            transaction_id = f"CASH-{sale_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}" if success else None
            return success, transaction_id, msg
            
        elif payment_method.lower() == PaymentMethod.MOMO.value:
            phone = kwargs.get('phone_number', '')
            reference = kwargs.get('reference', '')
            provider = kwargs.get('provider', 'mtn')
            return process_momo_payment(amount_paid, total_amount, sale_id, phone, reference, provider)
            
        elif payment_method.lower() == PaymentMethod.CARD.value:
            card_num = kwargs.get('card_number', '')
            expiry = kwargs.get('expiry', '')
            cvv = kwargs.get('cvv', '')
            cardholder = kwargs.get('cardholder_name', 'UNKNOWN')
            return process_card_payment(amount_paid, total_amount, sale_id, card_num, expiry, cvv, cardholder)
            
        elif payment_method.lower() == PaymentMethod.BANK_TRANSFER.value:
            account = kwargs.get('account_holder', '')
            reference = kwargs.get('reference', '')
            return process_bank_transfer(amount_paid, total_amount, sale_id, account, reference)
            
        else:
            return False, None, f"Unknown payment method: {payment_method}"
            
    except Exception as e:
        logger.error(f"[PAYMENT] Error processing payment: {str(e)}")
        return False, None, f"Payment processing error: {str(e)}"
