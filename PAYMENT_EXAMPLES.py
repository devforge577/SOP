"""
Payment System Examples & Integration Tests

Comprehensive examples showing how to use the payment system
in various real-world scenarios.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from datetime import datetime, timedelta
from services.payment_service import PaymentService, process_cash_checkout
from modules.payments import (
    get_payment_summary,
    get_pending_payments,
    reconcile_payments,
    get_cash_drawer_summary,
    process_refund
)


# ══════════════════════════════════════════════════════════════════════════════
# EXAMPLE 1: SIMPLE CASH CHECKOUT
# ══════════════════════════════════════════════════════════════════════════════

def example_cash_checkout():
    """Example: Customer pays with cash"""
    print("\n" + "="*70)
    print("EXAMPLE 1: SIMPLE CASH CHECKOUT")
    print("="*70)
    
    # Sale details
    sale_id = 100
    total_amount = 1159.97
    amount_tendered = 1200.00
    cashier_id = 3  # Cashier user
    
    # Process cash payment
    success, txn_id, change, msg = PaymentService.checkout_payment(
        user_id=cashier_id,
        amount_paid=amount_tendered,
        total_amount=total_amount,
        sale_id=sale_id,
        payment_method='cash'
    )
    
    if success:
        print(f"[SUCCESS] Cash payment processed")
        print(f"  Sale ID: {sale_id}")
        print(f"  Total: GHS {total_amount:.2f}")
        print(f"  Paid: GHS {amount_tendered:.2f}")
        print(f"  Change: GHS {change:.2f}")
        print(f"  Transaction: {txn_id}")
        print(f"  Message: {msg}")
    else:
        print(f"[FAILED] {msg}")


# ══════════════════════════════════════════════════════════════════════════════
# EXAMPLE 2: MOMO PAYMENT WITH FEE CALCULATION
# ══════════════════════════════════════════════════════════════════════════════

def example_momo_checkout():
    """Example: Customer pays with Mobile Money"""
    print("\n" + "="*70)
    print("EXAMPLE 2: MOMO PAYMENT WITH FEE")
    print("="*70)
    
    # Sale details
    sale_id = 101
    total_amount = 500.00
    amount_tendered = 508.00  # Covering fee
    
    # MoMo transaction details
    phone_number = "0541234567"
    reference = "INV20260402001234"
    provider = "mtn"
    
    # Calculate expected fee
    fee_percentage = 1.5  # MoMo fee
    expected_fee = amount_tendered * (fee_percentage / 100)
    net_amount = amount_tendered - expected_fee
    
    print(f"Amount Paid: GHS {amount_tendered:.2f}")
    print(f"Expected Fee (1.5%): GHS {expected_fee:.2f}")
    print(f"Net Amount: GHS {net_amount:.2f}")
    print(f"Total Needed: GHS {total_amount:.2f}")
    
    # Process MoMo payment
    success, txn_id, msg = PaymentService.checkout_payment(
        user_id=3,
        amount_paid=amount_tendered,
        total_amount=total_amount,
        sale_id=sale_id,
        payment_method='momo',
        phone_number=phone_number,
        reference=reference,
        provider=provider
    )
    
    if success:
        print(f"\n[SUCCESS] MoMo payment processed")
        print(f"  Transaction ID: {txn_id}")
        print(f"  Reference: {reference}")
        print(f"  Status: COMPLETED")
        print(f"  Message: {msg}")
    else:
        print(f"\n[FAILED] {msg}")


# ══════════════════════════════════════════════════════════════════════════════
# EXAMPLE 3: CARD PAYMENT WITH GATEWAY
# ══════════════════════════════════════════════════════════════════════════════

def example_card_checkout():
    """Example: Customer pays with card"""
    print("\n" + "="*70)
    print("EXAMPLE 3: CARD PAYMENT WITH GATEWAY")
    print("="*70)
    
    # Sale details
    sale_id = 102
    total_amount = 2500.00
    amount_tendered = 2564.00  # Covering fee
    
    # Card details (TEST card)
    card_number = "4111111111111111"  # Paystack test card
    expiry = "12/25"
    cvv = "123"
    cardholder_name = "JOHN DOE"
    
    # Calculate expected fee
    fee_percentage = 2.5  # Card fee
    expected_fee = amount_tendered * (fee_percentage / 100)
    net_amount = amount_tendered - expected_fee
    
    print(f"Amount Paid: GHS {amount_tendered:.2f}")
    print(f"Expected Fee (2.5%): GHS {expected_fee:.2f}")
    print(f"Net Amount: GHS {net_amount:.2f}")
    print(f"Card Ending: ****{card_number[-4:]}")
    
    # Process card payment
    success, txn_id, msg = PaymentService.checkout_payment(
        user_id=3,
        amount_paid=amount_tendered,
        total_amount=total_amount,
        sale_id=sale_id,
        payment_method='card',
        card_number=card_number,
        expiry=expiry,
        cvv=cvv,
        cardholder_name=cardholder_name
    )
    
    if success:
        print(f"\n[SUCCESS] Card payment processed")
        print(f"  Transaction ID: {txn_id}")
        print(f"  Status: COMPLETED")
        print(f"  Message: {msg}")
    else:
        print(f"\n[FAILED] {msg}")


# ══════════════════════════════════════════════════════════════════════════════
# EXAMPLE 4: BANK TRANSFER (PENDING VERIFICATION)
# ══════════════════════════════════════════════════════════════════════════════

def example_bank_transfer():
    """Example: B2B payment via bank transfer"""
    print("\n" + "="*70)
    print("EXAMPLE 4: BANK TRANSFER (PENDING)")
    print("="*70)
    
    # Sale details
    sale_id = 103
    total_amount = 50000.00
    amount_paid = 50000.00
    
    # Bank transfer details
    account_holder = "ABC Trading Ltd"
    reference = "BANK-INV-20260402-001"
    
    print(f"Amount: GHS {amount_paid:.2f}")
    print(f"Account: {account_holder}")
    print(f"Reference: {reference}")
    
    # Process bank transfer (will be PENDING)
    success, txn_id, msg = PaymentService.checkout_payment(
        user_id=3,
        amount_paid=amount_paid,
        total_amount=total_amount,
        sale_id=sale_id,
        payment_method='bank_transfer',
        account_holder=account_holder,
        reference=reference
    )
    
    if success:
        print(f"\n[SUCCESS] Bank transfer initiated")
        print(f"  Transaction ID: {txn_id}")
        print(f"  Status: PENDING VERIFICATION")
        print(f"  Message: {msg}")
    else:
        print(f"\n[FAILED] {msg}")


# ══════════════════════════════════════════════════════════════════════════════
# EXAMPLE 5: PAYMENT SUMMARY & REPORTING
# ══════════════════════════════════════════════════════════════════════════════

def example_payment_summary():
    """Example: Manager views payment summary"""
    print("\n" + "="*70)
    print("EXAMPLE 5: PAYMENT SUMMARY REPORT")
    print("="*70)
    
    # Get today's payment summary
    today = datetime.now().strftime('%Y-%m-%d')
    
    success, summary = PaymentService.get_payment_report(
        user_id=2,  # Manager
        start_date=today,
        end_date=today
    )
    
    if success:
        print(f"\n[SUCCESS] Payment Report Generated")
        print(f"  Period: {summary['period']}")
        print(f"  Total Transactions: {summary['total_transactions']}")
        print(f"  Total Revenue: GHS {summary['total_revenue']:.2f}")
        print(f"  Total Fees: GHS {summary['total_fees']:.2f}")
        print(f"  Net Revenue: GHS {summary['net_revenue']:.2f}")
        
        print(f"\n  Breakdown by Method:")
        for method, data in summary['by_method'].items():
            print(f"\n    {method.upper()}")
            print(f"      Transactions: {data['transactions']}")
            print(f"      Total: GHS {data['total_amount']:.2f}")
            print(f"      Fees: GHS {data['fees']:.2f}")
            print(f"      Net: GHS {data['net_amount']:.2f}")
            print(f"      Average: GHS {data['avg_amount']:.2f}")
    else:
        print(f"[FAILED] Could not generate report")


# ══════════════════════════════════════════════════════════════════════════════
# EXAMPLE 6: DAILY RECONCILIATION
# ══════════════════════════════════════════════════════════════════════════════

def example_reconciliation():
    """Example: Manager reconciles daily payments"""
    print("\n" + "="*70)
    print("EXAMPLE 6: DAILY RECONCILIATION")
    print("="*70)
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    success, report = PaymentService.reconcile_day(
        user_id=2,  # Manager
        date=today
    )
    
    if success:
        print(f"\n[SUCCESS] Reconciliation Report")
        print(f"  Date: {report['reconciliation_date']}")
        print(f"  Status: {report['status']}")
        print(f"  Generated: {report['timestamp']}")
        
        print(f"\n  Transaction Summary:")
        for txn in report['transactions']:
            print(f"    {txn['method'].upper()} ({txn['status']}):")
            print(f"      Count: {txn['count']}")
            print(f"      Amount: GHS {txn['amount']:.2f}")
            print(f"      Fees: GHS {txn['fees']:.2f}")
        
        print(f"\n  Daily Totals:")
        print(f"    Completed: GHS {report['totals']['completed']:.2f}")
        print(f"    Pending: GHS {report['totals']['pending']:.2f}")
        print(f"    Failed: GHS {report['totals']['failed']:.2f}")
        print(f"    Total: GHS {report['totals']['total']:.2f}")
    else:
        print(f"[FAILED] Reconciliation error")


# ══════════════════════════════════════════════════════════════════════════════
# EXAMPLE 7: CASH DRAWER SUMMARY
# ══════════════════════════════════════════════════════════════════════════════

def example_cash_drawer():
    """Example: Manager views cash drawer"""
    print("\n" + "="*70)
    print("EXAMPLE 7: CASH DRAWER SUMMARY")
    print("="*70)
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    success, drawer = PaymentService.get_cash_drawer(
        user_id=2,  # Manager
        date=today
    )
    
    if success:
        print(f"\n[SUCCESS] Cash Drawer Summary")
        print(f"  Date: {drawer['date']}")
        print(f"  Currency: {drawer['currency']}")
        print(f"  Transactions: {drawer['transactions']}")
        print(f"  Total Received: GHS {drawer['total_received']:.2f}")
        print(f"  Total Change Given: GHS {drawer['total_change']:.2f}")
        print(f"  Net Cash in Drawer: GHS {drawer['net_cash']:.2f}")
    else:
        print(f"[FAILED] Could not get drawer summary")


# ══════════════════════════════════════════════════════════════════════════════
# EXAMPLE 8: PENDING PAYMENTS
# ══════════════════════════════════════════════════════════════════════════════

def example_pending_payments():
    """Example: Manager checks pending payments"""
    print("\n" + "="*70)
    print("EXAMPLE 8: PENDING PAYMENTS")
    print("="*70)
    
    success, pending = PaymentService.get_pending_transactions(user_id=2)
    
    if success:
        if not pending:
            print(f"\n[INFO] No pending payments")
        else:
            print(f"\n[SUCCESS] Found {len(pending)} pending payments")
            
            for i, payment in enumerate(pending, 1):
                print(f"\n  Payment {i}:")
                print(f"    Sale #: {payment['sale_id']}")
                print(f"    Amount: GHS {payment['amount_paid']:.2f}")
                print(f"    Method: {payment['payment_method']}")
                print(f"    Reference: {payment['reference']}")
                print(f"    Date: {payment['payment_date']}")
    else:
        print(f"[FAILED] Permission denied")


# ══════════════════════════════════════════════════════════════════════════════
# EXAMPLE 9: PROCESS REFUND
# ══════════════════════════════════════════════════════════════════════════════

def example_refund():
    """Example: Manager processes refund"""
    print("\n" + "="*70)
    print("EXAMPLE 9: PROCESS REFUND")
    print("="*70)
    
    # Assume payment_id 100 exists
    payment_id = 100
    reason = "Customer requested - item defective"
    
    success, msg = PaymentService.process_refund_request(
        user_id=2,
        payment_id=payment_id,
        reason=reason
    )
    
    if success:
        print(f"\n[SUCCESS] Refund processed")
        print(f"  Payment ID: {payment_id}")
        print(f"  Reason: {reason}")
        print(f"  Message: {msg}")
    else:
        print(f"\n[FAILED] {msg}")


# ══════════════════════════════════════════════════════════════════════════════
# EXAMPLE 10: ERROR HANDLING
# ══════════════════════════════════════════════════════════════════════════════

def example_error_handling():
    """Example: Handling payment errors"""
    print("\n" + "="*70)
    print("EXAMPLE 10: ERROR HANDLING")
    print("="*70)
    
    # Test 1: Insufficient cash
    print("\n  Test 1: Insufficient Cash")
    print("  " + "-"*50)
    success, txn_id, msg = PaymentService.checkout_payment(
        user_id=3,
        amount_paid=100.00,
        total_amount=150.00,
        sale_id=999,
        payment_method='cash'
    )
    print(f"  Result: {msg}")
    
    # Test 2: Invalid payment method
    print("\n  Test 2: Invalid Payment Method")
    print("  " + "-"*50)
    success, txn_id, msg = PaymentService.checkout_payment(
        user_id=3,
        amount_paid=100.00,
        total_amount=100.00,
        sale_id=999,
        payment_method='invalid_method'
    )
    print(f"  Result: {msg}")
    
    # Test 3: Permission denied (user is not manager/cashier)
    print("\n  Test 3: Permission Denied")
    print("  " + "-"*50)
    success, txn_id, msg = PaymentService.checkout_payment(
        user_id=999,  # Non-existent user
        amount_paid=100.00,
        total_amount=100.00,
        sale_id=999,
        payment_method='cash'
    )
    print(f"  Result: {msg}")
    
    # Test 4: Invalid card details
    print("\n  Test 4: Invalid Card Details")
    print("  " + "-"*50)
    success, txn_id, msg = PaymentService.checkout_payment(
        user_id=3,
        amount_paid=200.00,
        total_amount=200.00,
        sale_id=999,
        payment_method='card',
        card_number='1234',  # Too short
        expiry='13/25',  # Invalid month
        cvv='12'  # Too short
    )
    print(f"  Result: {msg}")


# ══════════════════════════════════════════════════════════════════════════════
# COMPLETE POS WORKFLOW WITH PAYMENT
# ══════════════════════════════════════════════════════════════════════════════

def example_complete_workflow():
    """Example: Complete POS sale workflow"""
    print("\n" + "="*70)
    print("COMPLETE WORKFLOW: Customer Sale with Payment")
    print("="*70)
    
    # Step 1: Create sale
    print("\n1. Create Sale")
    print("  " + "-"*50)
    sale_id = 200
    items = [
        {'product': 'Keyboard', 'qty': 1, 'price': 79.99, 'subtotal': 79.99},
        {'product': 'Mouse', 'qty': 2, 'price': 29.99, 'subtotal': 59.98},
    ]
    
    subtotal = sum(item['subtotal'] for item in items)
    tax = 0  # No tax
    total = subtotal + tax
    
    print(f"  Sale ID: {sale_id}")
    for item in items:
        print(f"    - {item['product']}: GHS {item['subtotal']:.2f}")
    print(f"  Subtotal: GHS {subtotal:.2f}")
    print(f"  Tax: GHS {tax:.2f}")
    print(f"  Total: GHS {total:.2f}")
    
    # Step 2: Payment selection
    print("\n2. Customer Selects Payment Method: CASH")
    print("  " + "-"*50)
    payment_method = 'cash'
    amount_tendered = 150.00
    print(f"  Method: {payment_method.upper()}")
    print(f"  Amount Tendered: GHS {amount_tendered:.2f}")
    
    # Step 3: Process payment
    print("\n3. Process Payment")
    print("  " + "-"*50)
    success, txn_id, change, msg = PaymentService.checkout_payment(
        user_id=3,
        amount_paid=amount_tendered,
        total_amount=total,
        sale_id=sale_id,
        payment_method=payment_method
    )
    
    if success:
        print(f"  [SUCCESS] Payment Processed")
        print(f"    Transaction ID: {txn_id}")
        print(f"    Change: GHS {change:.2f}")
    else:
        print(f"  [FAILED] {msg}")
    
    # Step 4: Generate receipt
    print("\n4. Generate Receipt")
    print("  " + "-"*50)
    print(f"  " + "="*45)
    print(f"  {'RECEIPT':^45}")
    print(f"  " + "="*45)
    print(f"  Sale #: {sale_id}")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    for item in items:
        print(f"  {item['product']:20} x{item['qty']:2} {item['subtotal']:>10.2f}")
    print(f"  {'-'*45}")
    print(f"  {'Total':20} {'':16} {total:>10.2f}")
    print(f"  {'Paid':20} {'':16} {amount_tendered:>10.2f}")
    print(f"  {'Change':20} {'':16} {change:>10.2f}")
    print(f"  {'-'*45}")
    print(f"  Payment: {payment_method.upper()}")
    print(f"  " + "="*45)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "="*70)
    print("PAYMENT SYSTEM - COMPREHENSIVE EXAMPLES")
    print("="*70)
    
    try:
        # Run all examples
        example_cash_checkout()
        example_momo_checkout()
        example_card_checkout()
        example_bank_transfer()
        example_payment_summary()
        example_reconciliation()
        example_cash_drawer()
        example_pending_payments()
        example_refund()
        example_error_handling()
        example_complete_workflow()
        
        print("\n" + "="*70)
        print("ALL EXAMPLES COMPLETED")
        print("="*70)
        
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
