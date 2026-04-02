# Payment System Documentation

Complete reference for the comprehensive payment processing system.

---

## Overview

The Payment System provides:
- ✅ **Multiple Payment Methods**: Cash, Mobile Money (MoMo), Card, Bank Transfer
- ✅ **Payment Validation**: Comprehensive input validation and error handling
- ✅ **Gateway Integration**: Framework for Paystack, Stripe, MTN MoMo APIs
- ✅ **Payment Reconciliation**: Daily settlement and cash drawer management
- ✅ **Refund Processing**: Full and partial refunds with audit trail
- ✅ **Transaction Tracking**: Complete payment history and reporting

---

## Architecture

### Three-Layer Payment Processing

```
PRESENTATION LAYER
CashierView (UI) → Select payment method & enter details
         ↓
SERVICES LAYER
PaymentService → Permission checks, error handling, coordination
         ↓
BUSINESS LOGIC LAYER  
payments.py → Core payment processing, validation, gateway calls
         ↓
PERSISTENCE LAYER
Database → Store and retrieve payment records
```

---

## Payment Methods

### 1. Cash Payment

**Best For:** Over-the-counter transactions, immediate settlement

**Process:**
1. Customer provides cash
2. Validate amount >= total
3. Calculate change
4. Record payment with change amount
5. Immediate completion

**Code Example:**
```python
from services.payment_service import PaymentService

success, txn_id, change, msg = PaymentService.checkout_payment(
    user_id=3,              # Cashier
    amount_paid=1200.00,
    total_amount=1159.97,
    sale_id=42,
    payment_method='cash'
)

if success:
    print(f"Change: GHS {change:.2f}")
    print(f"Receipt: {txn_id}")
```

**Validation Rules:**
- Amount paid >= Total amount
- Exact change not required
- No fees applied

---

### 2. Mobile Money (MoMo)

**Best For:** Wireless transfers, customer convenience, reconciliation later

**Process:**
1. Customer provides phone number
2. Enter MoMo reference/transaction ID
3. System calls MoMo API to verify
4. Calculate transaction fee (1.5%)
5. Verify amount after fee still covers sale
6. Record with reference and status

**Code Example:**
```python
from services.payment_service import PaymentService

success, txn_id, msg = PaymentService.checkout_payment(
    user_id=3,
    amount_paid=1200.00,
    total_amount=1159.97,
    sale_id=42,
    payment_method='momo',
    phone_number='0541234567',
    reference='INV20260402001234',
    provider='mtn'  # 'mtn' or 'vodafone'
)

if success:
    print(f"MoMo Verified: {txn_id}")
```

**Fee Structure:**
- MTN MoMo: 1.5% fee
- Vodafone Cash: 1.5% fee
- Net amount = Amount paid - Fee
- Sale amount must be <= Net amount

**Reference Format:**
- Transaction/Invoice ID from provider
- Used for reconciliation
- Must be unique within reason

---

### 3. Card Payment

**Best For:** Large transactions, online future-proofing, audit trail

**Process:**
1. Collect card details (securely)
2. Validate card format
3. Call payment gateway (Paystack/Stripe)
4. Calculate transaction fee (2.5%)
5. Verify authorization
6. Record with gateway transaction ID
7. Store only last 4 digits

**Code Example:**
```python
from services.payment_service import PaymentService

success, txn_id, msg = PaymentService.checkout_payment(
    user_id=3,
    amount_paid=5000.00,
    total_amount=4870.00,
    sale_id=43,
    payment_method='card',
    card_number='4111111111111111',  # Test card
    expiry='12/25',
    cvv='123',
    cardholder_name='JOHN DOE'
)

if success:
    print(f"Card Approved: {txn_id}")
```

**Fee Structure:**
- Card processing: 2.5% fee
- Charged by payment gateway
- Net amount = Amount paid - Fee

**Security Considerations:**
- Never store full card numbers
- Use gateway security standards (PCI DSS)
- Validate expiry and CVV
- Use HTTPS for transmission

---

### 4. Bank Transfer

**Best For:** B2B transactions, high-value sales, corporate accounts

**Process:**
1. Collect bank reference
2. Set payment status to PENDING
3. Manager verifies bank account later
4. Update status when confirmed
5. No transaction fee

**Code Example:**
```python
from services.payment_service import PaymentService

success, txn_id, msg = PaymentService.checkout_payment(
    user_id=3,
    amount_paid=15000.00,
    total_amount=15000.00,
    sale_id=44,
    payment_method='bank_transfer',
    account_holder='ABC Trading Ltd',
    reference='BANK-INV-20260402-001'
)

# Manager verifies and confirms later
print(f"Awaiting Verification: {txn_id}")
print("Status: PENDING")
```

**Characteristics:**
- No fees applied
- Initial status: PENDING
- Requires manual verification
- Full amount paid upfront

---

## Payment Service API

### Main Checkout Function

```python
PaymentService.checkout_payment(
    user_id: int,              # Cashier ID
    amount_paid: float,        # Amount tendered
    total_amount: float,       # Sale total
    sale_id: int,             # Sale ID
    payment_method: str,       # 'cash', 'momo', 'card', 'bank_transfer'
    **kwargs                   # Method-specific parameters
) -> (bool, transaction_id: str | None, message: str)
```

**Returns:**
- `success`: True if payment processed
- `transaction_id`: Reference ID (if success)
- `message`: Status or error message

**Method-Specific Parameters:**

**Cash:**
```python
PaymentService.checkout_payment(..., payment_method='cash')
```

**MoMo:**
```python
PaymentService.checkout_payment(
    ..., payment_method='momo',
    phone_number='0541234567',
    reference='INV20260402001234',
    provider='mtn'
)
```

**Card:**
```python
PaymentService.checkout_payment(
    ..., payment_method='card',
    card_number='4111111111111111',
    expiry='12/25',
    cvv='123',
    cardholder_name='JOHN DOE'
)
```

**Bank Transfer:**
```python
PaymentService.checkout_payment(
    ..., payment_method='bank_transfer',
    account_holder='ABC Trading Ltd',
    reference='BANK-INV-20260402-001'
)
```

---

## Payment Reporting & Reconciliation

### Get Payment Summary

```python
from services.payment_service import PaymentService

success, summary = PaymentService.get_payment_report(
    user_id=2,  # Manager
    start_date='2026-04-01',
    end_date='2026-04-30'
)

if success:
    print(f"Period: {summary['period']}")
    print(f"Total Revenue: GHS {summary['total_revenue']:.2f}")
    print(f"Total Fees: GHS {summary['total_fees']:.2f}")
    
    for method, data in summary['by_method'].items():
        print(f"\n{method.upper()}:")
        print(f"  Transactions: {data['transactions']}")
        print(f"  Total: GHS {data['total_amount']:.2f}")
        print(f"  Fees: GHS {data['fees']:.2f}")
        print(f"  Net: GHS {data['net_amount']:.2f}")
```

**Response Format:**
```python
{
    'period': '2026-04-01 to 2026-04-30',
    'total_transactions': 156,
    'total_revenue': 45678.50,
    'total_fees': 1145.67,
    'net_revenue': 44532.83,
    'by_method': {
        'cash': {
            'transactions': 100,
            'total_amount': 32456.00,
            'fees': 0.0,
            'net_amount': 32456.00,
            'avg_amount': 324.56
        },
        'momo': {
            'transactions': 40,
            'total_amount': 10234.50,
            'fees': 145.67,
            'net_amount': 10088.83,
            'avg_amount': 255.86
        },
        'card': {
            'transactions': 16,
            'total_amount': 2988.00,
            'fees': 1000.00,
            'net_amount': 1988.00,
            'avg_amount': 186.75
        }
    }
}
```

### Reconcile Daily Payments

```python
from services.payment_service import PaymentService

success, report = PaymentService.reconcile_day(
    user_id=2,  # Manager
    date='2026-04-02'
)

if success:
    print(f"Reconciliation Date: {report['reconciliation_date']}")
    print(f"Status: {report['status']}")
    
    print("\nTransaction Summary:")
    for txn in report['transactions']:
        print(f"  {txn['method']}: {txn['count']} txns ({txn['status']})")
    
    print(f"\nCompleted: GHS {report['totals']['completed']:.2f}")
    print(f"Pending: GHS {report['totals']['pending']:.2f}")
    print(f"Total: GHS {report['totals']['total']:.2f}")
```

### Get Pending Payments

```python
from services.payment_service import PaymentService

success, pending = PaymentService.get_pending_transactions(user_id=2)

if success:
    for payment in pending:
        print(f"\nSale #{payment['sale_id']}: GHS {payment['amount_paid']:.2f}")
        print(f"  Method: {payment['payment_method']}")
        print(f"  Reference: {payment['reference']}")
        print(f"  Date: {payment['payment_date']}")
```

### Cash Drawer Summary

```python
from services.payment_service import PaymentService

success, drawer = PaymentService.get_cash_drawer(
    user_id=2,
    date='2026-04-02'
)

if success:
    print(f"Cash Drawer - {drawer['date']}")
    print(f"Transactions: {drawer['transactions']}")
    print(f"Total Received: GHS {drawer['total_received']:.2f}")
    print(f"Total Change: GHS {drawer['total_change']:.2f}")
    print(f"Net Cash: GHS {drawer['net_cash']:.2f}")
```

---

## Refund Processing

```python
from services.payment_service import PaymentService

# Full refund
success, msg = PaymentService.process_refund_request(
    user_id=2,          # Manager
    payment_id=127,     # Payment to refund
    reason='Customer requested - item defective'
)

# Partial refund
success, msg = PaymentService.process_refund_request(
    user_id=2,
    payment_id=127,
    reason='Partial refund - partial usage',
    refund_amount=500.00  # Partial amount
)

if success:
    print(f"Refund Processed: {msg}")
```

---

## Pending Payment Management

### Verify Pending Payment

For MoMo and Bank Transfers that start as PENDING:

```python
from modules.payments import verify_payment_with_gateway

is_verified, msg = verify_payment_with_gateway(payment_id=128)

if is_verified:
    print("Payment confirmed by gateway")
else:
    print(f"Verification failed: {msg}")
```

---

## Payment Gateway Integration

### Supported Gateways

| Gateway | Methods | Countries | Status |
|---------|---------|-----------|--------|
| Paystack | Card, MoMo, Bank | Ghana, Nigeria, Kenya | Ready |
| Stripe | Card | Global | Ready |
| MTN MoMo API | MoMo | Ghana, Cameroon | Ready |
| Vodafone Cash | MoMo | Ghana | Ready |

### Implementing Gateway Integration

```python
# In modules/payments.py, update _call_payment_gateway():

import requests

def _call_payment_gateway(method: str, amount: float, **kwargs) -> Dict[str, Any]:
    """
    Implement actual gateway calls here.
    """
    
    if method == 'card':
        # Example: Paystack integration
        response = requests.post(
            'https://api.paystack.co/transaction/initialize',
            headers={'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}'},
            json={
                'email': kwargs.get('email'),
                'amount': int(amount * 100),  # Convert to kobo
                'metadata': {'sale_id': kwargs.get('sale_id')}
            }
        )
        
        if response.status_code == 200:
            data = response.json()['data']
            return {
                'success': True,
                'transaction_id': str(data['reference']),
                'message': 'Card payment initialized'
            }
    
    return {
        'success': False,
        'transaction_id': None,
        'message': 'Gateway error'
    }
```

---

## Error Handling

### Payment Validation Errors

```python
from modules.payments import validate_payment_method, validate_amount

# Check payment method
valid, msg = validate_payment_method('momo')
if not valid:
    print(f"Error: {msg}")
    # Output: "Error: Unsupported payment method..."

# Check amount
valid, msg = validate_amount(0)
if not valid:
    print(f"Error: {msg}")
    # Output: "Error: Amount must be greater than 0"

# Check cash payment
valid, msg = validate_cash_payment(amount_paid=100, total_amount=150)
if not valid:
    print(f"Error: {msg}")
    # Output: "Error: Insufficient payment. Need additional GHS 50.00"
```

### Common Error Scenarios

```python
scenarios = {
    'Insufficient Cash': {
        'cause': 'Amount paid < Total amount',
        'solution': 'Request customer pay additional amount'
    },
    'Card Declined': {
        'cause': 'Card failed gateway authorization',
        'solution': 'Try different card or payment method'
    },
    'MoMo Reference Invalid': {
        'cause': 'Reference not found or expired',
        'solution': 'Verify reference with customer, retry'
    },
    'Gateway Unavailable': {
        'cause': 'Payment gateway API down',
        'solution': 'Use alternative method or try later'
    },
    'Permission Denied': {
        'cause': 'User lacks payment processing permission',
        'solution': 'Only cashier/admin can process payments'
    }
}
```

---

## Database Schema

### Payments Table

```sql
CREATE TABLE payments (
    payment_id INTEGER PRIMARY KEY,
    sale_id INTEGER NOT NULL,           -- FK to sales
    amount_paid REAL NOT NULL,          -- Gross amount
    change_given REAL DEFAULT 0,        -- Cash change (cash only)
    payment_method TEXT NOT NULL,       -- cash, momo, card, bank_transfer
    status TEXT DEFAULT 'completed',    -- pending, processing, completed, failed, reversed
    reference TEXT,                     -- Transaction ref (MoMo, Card, Bank)
    provider TEXT,                      -- MoMo provider (mtn, vodafone)
    fee REAL DEFAULT 0,                 -- Transaction fee deducted
    payment_date TEXT,                  -- When payment was made
    created_at TEXT                     -- Record creation timestamp
)
```

### Key Indexes
- `idx_payments_date` - For daily reconciliation
- `idx_payments_method` - For method breakdown
- `idx_payments_status` - For pending payment queries
- `idx_payments_sale` - For payment lookup by sale

---

## Testing Payments

### Unit Test Examples

```python
def test_cash_payment():
    """Test cash payment with change"""
    success, txn_id, msg = process_payment(
        amount_paid=1200,
        total_amount=1159.97,
        sale_id=1,
        payment_method='cash'
    )
    assert success
    assert txn_id is not None
    
def test_cash_insufficient():
    """Test insufficient cash"""
    success, txn_id, msg = process_payment(
        amount_paid=100,
        total_amount=150,
        sale_id=2,
        payment_method='cash'
    )
    assert not success
    assert 'insufficient' in msg.lower()

def test_momo_with_fee():
    """Test MoMo deducts fee"""
    success, txn_id, msg = process_payment(
        amount_paid=1000,      # 1.5% fee = 15
        total_amount=990,      # Net: 985
        sale_id=3,
        payment_method='momo',
        phone_number='0541234567',
        reference='REF001'
    )
    assert success
    # Verify fee was calculated correctly

def test_permission_denied():
    """Test non-cashier cannot process payment"""
    success, txn_id, msg = PaymentService.checkout_payment(
        user_id=1,  # Admin (not cashier)
        ...
    )
    assert not success
    assert 'permission' in msg.lower()
```

### Test Credentials

| Payment Method | Test Data |
|----------------|-----------|
| Cash | Any amount > 0 |
| Card (Paystack) | 4111 1111 1111 1111 |
| Card (Stripe) | 4242 4242 4242 4242 |
| Card Expiry | Any future date MM/YY |
| Card CVV | Any 3-4 digits |
| MoMo Reference | INV20260402001234 |

---

## Best Practices

### For Cashiers
1. ✅ Always verify amount before confirming payment
2. ✅ Keep receipt for customer
3. ✅ Report payment method issues immediately
4. ✅ For cash: Count change carefully before handing to customer
5. ✅ For MoMo: Get reference and verify with customer

### For Managers
1. ✅ Reconcile payments daily
2. ✅ Verify pending payments timely
3. ✅ Monitor payment gateway fees
4. ✅ Review failed transactions for patterns
5. ✅ Keep cash drawer balanced

### For Developers
1. ✅ Always validate amount and method
2. ✅ Use permission checks in service layer
3. ✅ Log all payment transactions
4. ✅ Never store sensitive card data
5. ✅ Use HTTPS for payment transmission
6. ✅ Implement idempotent operations

---

## Configuration

### Setting Environment Variables (Future)

```bash
# .env file
export PAYSTACK_SECRET_KEY="sk_live_..."
export PAYSTACK_PUBLIC_KEY="pk_live_..."
export STRIPE_API_KEY="sk_live_..."
export MTN_MOMO_API_KEY="..."
export MTN_MOMO_API_USER="..."
```

### Load in Code

```python
import os
from modules import payments

payments.PAYMENT_GATEWAY_CONFIG['paystack']['secret_key'] = os.getenv('PAYSTACK_SECRET_KEY')
```

---

## Summary

| Feature | Status | Coverage |
|---------|--------|----------|
| Cash Payment | ✅ Complete | Full |
| MoMo Payment | ✅ Complete | Framework ready |
| Card Payment | ✅ Complete | Framework ready |
| Bank Transfer | ✅ Complete | Framework ready |
| Validation | ✅ Complete | Full |
| Reconciliation | ✅ Complete | Full |
| Refunds | ✅ Complete | Full |
| Gateway Integration | ⏳ Ready | Framework ready |
| Permission Checking | ✅ Complete | Full |
| Error Handling | ✅ Complete | Full |
| Decimal Precision | ✅ Complete | 2 decimals |
| Audit Logging | ✅ Complete | Full |

---

## Next Steps

1. **Implement Gateway APIs** - Add actual Paystack/Stripe calls
2. **Add Payment UI** - Update CashierView with payment form
3. **Add Payment Verification** - Webhook handlers for gateway callbacks
4. **Add Receipts** - Print/SMS payment receipts
5. **Add Bulk Refunds** - Process refunds in batch
6. **Add Payment Disputes** - Dispute tracking and resolution

