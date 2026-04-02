# Application Layer: Business Logic Reference Guide

Complete reference for implementing and using the four core business domains.

---

## 1. Sales Processing Module

**File:** `modules/sales.py`  
**Domain:** Transaction management and e-commerce operations

### Function Reference

| Function | Purpose | Returns | Permission |
|----------|---------|---------|-----------|
| `cart_add_item()` | Add product to cart | (cart, bool, msg) | cashier+ |
| `cart_remove_item()` | Remove product from cart | cart | cashier+ |
| `cart_update_quantity()` | Change item quantity | (cart, bool, msg) | cashier+ |
| `cart_clear()` | Empty cart | cart | cashier+ |
| `cart_totals()` | Calculate subtotal, tax, total | dict | cashier+ |
| `get_cart_item_count()` | Count items in cart | int | cashier+ |
| `get_cart_summary()` | Get cart display text | str | cashier+ |
| `process_sale()` | Complete transaction | (bool, sale_id, change, msg) | cashier+ |
| `get_sale_details()` | Retrieve transaction | dict | cashier+ |
| `generate_receipt()` | Format receipt text | str | cashier+ |
| `void_sale()` | Cancel transaction | (bool, msg) | manager+ |
| `get_today_sales()` | Today's transactions | [dict] | manager+ |
| `get_sales_by_date()` | Date range sales | [dict] | manager+ |

### Code Examples

#### Adding Items to Cart
```python
from modules.sales import cart_add_item, cart_totals

# Initialize cart
cart = []

# Add first item
product_1 = {
    'product_id': 1,
    'product_name': 'Laptop',
    'price': 999.99,
    'stock': 10
}
cart, success, msg = cart_add_item(cart, product_1, quantity=1)
if not success:
    print(f"Error: {msg}")  # e.g., "Out of stock"

# Add second item
product_2 = {
    'product_id': 2,
    'product_name': 'Mouse',
    'price': 29.99,
    'stock': 50
}
cart, success, msg = cart_add_item(cart, product_2, quantity=2)

# View cart
print(cart)
# Output:
# [
#   {'product_id': 1, 'product_name': 'Laptop', 'unit_price': 999.99, 
#    'quantity': 1, 'subtotal': 999.99},
#   {'product_id': 2, 'product_name': 'Mouse', 'unit_price': 29.99, 
#    'quantity': 2, 'subtotal': 59.98}
# ]
```

#### Processing Checkout
```python
from modules.sales import process_sale, generate_receipt

# Process payment
success, sale_id, change, msg = process_sale(
    cart=cart,
    user_id=3,  # Cashier user_id (seeded as 'cashier' user)
    payment_method='cash',
    amount_paid=1200.00,
    discount=50.00,
    tax_rate=0.0,
    customer_id=None  # Optional
)

if success:
    print(f"Sale #{sale_id} completed")
    print(f"Change: ${change:.2f}")
    
    # Generate receipt
    receipt = generate_receipt(sale_id, store_name="My Store")
    print(receipt)
else:
    print(f"Checkout failed: {msg}")
```

### Business Validation Rules

```
Cart Addition:
  ✓ quantity > 0
  ✓ stock >= quantity + items_already_in_cart
  ✓ Calculate subtotal: quantity * unit_price

Checkout:
  ✓ cart not empty
  ✓ payment_method in ['cash', 'momo', 'card']
  ✓ amount_paid >= total_amount
  ✓ Perform in single transaction
  ✓ Deduct inventory after recording sale
```

---

## 2. Inventory Control Module

**File:** `modules/products.py`  
**Domain:** Product catalog and stock management

### Function Reference

| Function | Purpose | Returns | Permission |
|----------|---------|---------|-----------|
| `get_all_products()` | All products with inventory | [dict] | all |
| `search_products()` | Search by name/category | [dict] | all |
| `get_product_by_barcode()` | Barcode lookup (POS) | dict or None | all |
| `get_product_by_id()` | Get by product ID | dict or None | all |
| `get_categories()` | All categories | [str] | all |
| `get_low_stock_products()` | Alert products | [dict] | manager+ |
| `add_product()` | Create new product | (bool, msg) | manager+ |
| `update_product()` | Edit product details | (bool, msg) | manager+ |
| `delete_product()` | Deactivate/delete product | (bool, msg) | manager+ |
| `restore_product()` | Reactivate product | (bool, msg) | manager+ |
| `adjust_stock()` | Add/remove from inventory | (bool, quantity) | manager+ |
| `get_product_with_details()` | Full product info | dict or None | all |
| `get_products_by_category()` | Filter by category | [dict] | all |

### Code Examples

#### Adding Products to Catalog
```python
from modules.products import add_product, get_categories

# Add new product
success, msg = add_product(
    product_name='Wireless Mouse',
    category='Electronics',
    price=49.99,
    barcode='BAR123456',
    supplier='TechCorp Inc',
    initial_stock=100,
    low_stock_alert=20,
    user_id=2  # Manager ID (seeded as 'manager' user)
)

if success:
    print(f"Product added: {msg}")  # "Product added successfully (ID: 42)"
else:
    print(f"Error: {msg}")  # e.g., "Product with that barcode already exists"

# Get categories for dropdown
categories = get_categories()
# Output: ['Electronics', 'Furniture', 'Accessories', 'General']
```

#### Managing Stock Levels
```python
from modules.products import adjust_stock, get_low_stock_products

# Receive new stock
success, new_qty = adjust_stock(
    product_id=42,
    quantity_change=50,  # Add 50 units
    reason="Supplier delivery #2024-001",
    user_id=2  # Manager ID
)

if success:
    print(f"Stock updated to {new_qty} units")

# Check for low stock
low_stock = get_low_stock_products()
for product in low_stock:
    print(f"{product['product_name']}: {product['stock']} / {product['low_stock_alert']}")
    # Output:
    # USB Cable: 3 / 20
    # Keyboard: 7 / 15
```

#### Searching Products
```python
from modules.products import search_products, get_product_by_barcode

# Search by keyword
results = search_products('mouse')
# Output matches: product name, category, or barcode

# Quick barcode lookup (for POS)
product = get_product_by_barcode('BAR123456')
if product:
    print(f"Found: {product['product_name']} (${product['price']})")
    print(f"Stock: {product['stock']} available")
else:
    print("Product not found")
```

### Inventory Validation Rules

```
Product Creation:
  ✓ product_name not empty
  ✓ category not empty (defaults to "General")
  ✓ price >= 0
  ✓ barcode unique (if provided)
  ✓ initial_stock >= 0

Stock Adjustment:
  ✓ new_qty >= 0 (no negative inventory)
  ✓ Log reason for audit trail
  ✓ Track user making change

Product Deletion:
  ✓ If has sales history: soft delete (is_active = 0)
  ✓ If no sales history: hard delete (preserve data)
```

---

## 3. Payment Handling Module

**File:** `modules/sales.py` (payment logic)  
**Domain:** Payment processing and reconciliation

### Payment Flow

```
Customer → Amount Paid
    ↓
Validate Payment:
  ✓ Method is valid (cash/momo/card)
  ✓ Amount >= Total
    ↓
Calculate Change:
  change = amount_paid - total_amount
    ↓
Record Transaction:
  INSERT INTO payments (sale_id, amount_paid, change_given, method)
    ↓
Return:
  ✓ Success status
  ✓ Change amount
  ✓ Message
```

### Code Examples

#### Checkout with Payment
```python
from modules.sales import process_sale

# Sale details
cart_total = 1523.47
customer_payment = 1600.00
payment_method = 'cash'

# Process sale (includes payment)
success, sale_id, change, msg = process_sale(
    cart=cart,
    user_id=3,  # Cashier ID
    payment_method=payment_method,
    amount_paid=customer_payment,
    discount=0,
    tax_rate=0.0
)

if success:
    print(f"Total: ${cart_total:.2f}")
    print(f"Paid:  ${customer_payment:.2f}")
    print(f"Change: ${change:.2f}")  # Automatically calculated
else:
    print(f"Error: {msg}")  # e.g., "Amount paid is less than total"
```

#### Payment Analytics
```python
from modules.reports import get_payment_method_breakdown

# Analyze payments by method
breakdown = get_payment_method_breakdown(
    start_date='2024-01-01',
    end_date='2024-01-31'
)

for method in breakdown:
    print(f"{method['payment_method'].upper()}:")
    print(f"  Transactions: {method['transactions']}")
    print(f"  Revenue: ${method['revenue']:.2f}")
    print(f"  Percentage: {method['percentage']:.1f}%")
    print(f"  Avg Value: ${method['avg_transaction_value']:.2f}")

# Output example:
# CASH:
#   Transactions: 150
#   Revenue: $45,234.50
#   Percentage: 60.5%
#   Avg Value: $301.56
# MOMO:
#   Transactions: 80
#   Revenue: $25,123.75
#   Percentage: 33.6%
#   Avg Value: $314.05
# CARD:
#   Transactions: 10
#   Revenue: $4,141.75
#   Percentage: 5.5%
#   Avg Value: $414.18
```

### Payment Validation Rules

```
Payment Method Validation:
  ✓ Accepted: 'cash', 'momo', 'card'
  ✓ Case insensitive in code

Amount Validation:
  ✓ amount_paid must be numeric
  ✓ amount_paid >= sale_total
  ✓ Reject short payments

Change Calculation:
  ✓ Accurate to 2 decimals
  ✓ change = amount_paid - total
  ✓ No floating point errors
```

---

## 4. Report Generation Module

**File:** `modules/reports.py`  
**Domain:** Business analytics and reporting

### Function Reference

| Function | Purpose | Returns | Permission |
|----------|---------|---------|-----------|
| `get_daily_summary()` | Today's totals | dict | manager+ |
| `get_sales_by_date_range()` | Period totals | [dict] | manager+ |
| `get_top_products()` | Bestsellers | [dict] | manager+ |
| `get_payment_method_breakdown()` | Payment analysis | [dict] | manager+ |
| `get_cashier_performance()` | Staff metrics | [dict] | manager+ |
| `get_inventory_report()` | Stock status | [dict] | manager+ |
| `get_low_performing_products()` | Slow movers | [dict] | manager+ |
| `get_recent_transactions()` | Latest sales | [dict] | manager+ |

### Code Examples

#### Daily Dashboard
```python
from modules.reports import get_daily_summary, get_top_products

# Get today's summary
today = get_daily_summary()  # date defaults to today

print(f"Today's Performance")
print(f"  Transactions: {today['total_transactions']}")
print(f"  Revenue: ${today['total_revenue']:.2f}")
print(f"  Average Sale: ${today['avg_sale_value']:.2f}")
print(f"  Discounts: ${today['total_discounts']:.2f}")
print(f"  Tax: ${today['total_tax']:.2f}")
print(f"  Net: ${today['net_revenue']:.2f}")

# Top products today
top_5 = get_top_products(limit=5)
for i, product in enumerate(top_5, 1):
    print(f"{i}. {product['product_name']}: {product['units_sold']} units (${product['revenue']:.2f})")
```

#### Period Analysis
```python
from modules.reports import get_sales_by_date_range

# Monthly sales trend
sales = get_sales_by_date_range(
    start_date='2024-01-01',
    end_date='2024-01-31'
)

total_revenue = 0
for day in sales:
    print(f"{day['sale_date']}: {day['total_transactions']} tx | ${day['total_revenue']:.2f}")
    total_revenue += day['total_revenue']

print(f"\nMonth Total: ${total_revenue:.2f}")
```

#### Staff Performance
```python
from modules.reports import get_cashier_performance

# Month performance
performance = get_cashier_performance(
    start_date='2024-01-01',
    end_date='2024-01-31'
)

for cashier in performance:
    print(f"{cashier['cashier']} ({cashier['role']}):")
    print(f"  Sales: {cashier['transactions']}")
    print(f"  Revenue: ${cashier['revenue']:.2f}")
    print(f"  Avg Sale: ${cashier['avg_sale_value']:.2f}")
    print(f"  Customers: {cashier['unique_customers']}")
```

#### Inventory Status
```python
from modules.reports import get_inventory_report

# Check stock status
inventory = get_inventory_report()

out_of_stock = [p for p in inventory if p['status'] == 'out_of_stock']
low_stock = [p for p in inventory if p['status'] == 'low_stock']

print(f"Out of Stock: {len(out_of_stock)} products")
for product in out_of_stock:
    print(f"  - {product['product_name']}")

print(f"\nLow Stock: {len(low_stock)} products")
for product in low_stock:
    print(f"  - {product['product_name']}: {product['quantity']} / {product['low_stock_alert']}")

total_value = sum(p['value'] for p in inventory)
print(f"\nTotal Inventory Value: ${total_value:,.2f}")
```

### Report Generation Rules

```
Date Handling:
  ✓ Defaults to today if not specified
  ✓ Uses YYYY-MM-DD format
  ✓ Includes full date range (both inclusive)

Calculations:
  ✓ All financial to 2 decimals
  ✓ Percentages to 1-2 decimals
  ✓ Counts as integers

Accuracy:
  ✓ No rounding errors
  ✓ Double-check aggregations
  ✓ Handle zero-transaction days gracefully
```

---

## Integration Example: Complete Sale Flow

```python
# === CASHIER POS WORKFLOW ===

# Step 1: Search for products
from modules.products import search_products, get_product_by_barcode

products = search_products('laptop')  # Search results

# Step 2: Build shopping cart
from modules.sales import cart_add_item, cart_totals

cart = []
for product in user_selected_products:
    cart, ok, msg = cart_add_item(cart, product, quantity=1)
    if not ok:
        print(f"Cannot add {product['product_name']}: {msg}")

# Step 3: Calculate totals
totals = cart_totals(
    cart,
    discount=user_entered_discount,
    tax_rate=0.0  # or 0.15 for 15% tax
)

# Display to user:
# Subtotal: $1,059.97
# Discount: -$50.00
# After:    $1,009.97
# Tax:      $0.00
# Total:    $1,009.97

# Step 4: Process payment
from modules.sales import process_sale, generate_receipt

success, sale_id, change, msg = process_sale(
    cart=cart,
    user_id=cashier_id,
    payment_method=payment_method,
    amount_paid=amount_tendered,
    discount=user_discount,
    tax_rate=0.0
)

if success:
    # Step 5: Generate receipt
    receipt = generate_receipt(sale_id)
    print(receipt)  # Print or display
    
    # Step 6: Can now query sale
    from modules.sales import get_sale_details
    details = get_sale_details(sale_id)
    # Use for receipt, customer verification, etc.
else:
    print(f"Sale failed: {msg}")

# === END OF DAY WORKFLOW ===

# Management reviews daily performance
from modules.reports import (
    get_daily_summary,
    get_top_products,
    get_payment_method_breakdown,
    get_cashier_performance
)

daily = get_daily_summary()
print(f"Today Revenue: ${daily['total_revenue']:.2f}")

top_10 = get_top_products(limit=10)
print("Top Products:")
for i, p in enumerate(top_10, 1):
    print(f"  {i}. {p['product_name']}: {p['units_sold']} units")

payment_methods = get_payment_method_breakdown()
print("Payment Methods:")
for method in payment_methods:
    print(f"  {method['payment_method']}: {method['percentage']:.1f}%")

cashiers = get_cashier_performance()
print("Staff Performance:")
for c in cashiers:
    print(f"  {c['cashier']}: ${c['revenue']:.2f}")
```

---

## Error Handling Pattern

All business logic functions follow this pattern:

```python
from typing import Tuple, Optional

def operation(...) -> Tuple[bool, Optional[Result], str]:
    """
    Consistent return pattern for all operations.
    
    Returns:
        (success: bool, result: Optional[data], message: str)
    
    On Error:
        (False, None, "Error description: specific detail")
        
    On Success:
        (True, result_data, "Success: action completed")
    """
    
    try:
        # Validate inputs
        if not valid_input:
            return False, None, f"Validation error: {reason}"
        
        # Business logic
        result = perform_operation()
        
        # Return success
        return True, result, f"Success: {description}"
        
    except Exception as e:
        logger.error(f"Operation error: {e}")
        return False, None, f"Error: {str(e)}"


# Usage pattern
success, result, msg = operation(parameters)

if success:
    # Use result
    print(msg)
else:
    # Handle error
    print(f"Failed: {msg}")
```

---

## Testing Business Logic

```python
import pytest
from modules.sales import cart_add_item, process_sale, cart_totals
from modules.products import add_product, adjust_stock
from modules.reports import get_daily_summary

def test_cart_operations():
    """Test shopping cart functionality"""
    cart = []
    product = {'product_id': 1, 'product_name': 'Test', 'price': 100, 'stock': 10}
    
    # Add item
    cart, ok, msg = cart_add_item(cart, product, 2)
    assert ok
    assert len(cart) == 1
    assert cart[0]['quantity'] == 2
    assert cart[0]['subtotal'] == 200
    
    # Invalid quantity
    cart, ok, msg = cart_add_item(cart, product, 0)
    assert not ok

def test_checkout():
    """Test sale processing"""
    cart = [{'product_id': 1, 'unit_price': 100, 'quantity': 2, 'subtotal': 200}]
    
    success, sale_id, change, msg = process_sale(
        cart, user_id=1, payment_method='cash',
        amount_paid=250.00
    )
    
    assert success
    assert sale_id is not None
    assert change == 50.00

def test_inventory():
    """Test stock management"""
    success, msg = add_product('Test', 'Test', 99.99, initial_stock=100)
    assert success
    
    # Adjust stock
    success, qty = adjust_stock(product_id, 50, 'Test adjustment')
    assert success
    assert qty == 150

def test_reporting():
    """Test report generation"""
    daily = get_daily_summary()
    assert 'total_revenue' in daily
    assert 'total_transactions' in daily
    assert daily['total_revenue'] >= 0
```

---

## Summary Table

| Domain | Purpose | Key Files | Permissions |
|--------|---------|-----------|------------|
| **Sales Processing** | Transaction handling | modules/sales.py | Cashier+ |
| **Inventory Control** | Stock management | modules/products.py | Manager+ |
| **Payment Handling** | Payment processing | modules/sales.py | Cashier+ |
| **Report Generation** | Analytics | modules/reports.py | Manager+ |

All maintain:
- ✓ Data integrity (transactions/constraints)
- ✓ Input validation
- ✓ Audit logging
- ✓ Consistent error handling
- ✓ No UI dependencies
