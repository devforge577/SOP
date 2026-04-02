# Application Layer: Business Logic

The Application Layer contains the core business logic that drives the POS system. This layer is independent of the user interface and implements pure business rules.

## Architecture Overview

```
┌─────────────────────────────────────────┐
│  PRESENTATION LAYER (Tkinter Views)    │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│  APPLICATION SERVICES LAYER            │
│  (Coordinates & Permission Checks)     │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│  APPLICATION LAYER (Business Logic)    │ ← YOU ARE HERE
│  ├─ Sales Processing                   │
│  ├─ Inventory Control                  │
│  ├─ Payment Handling                   │
│  └─ Report Generation                  │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│  PERSISTENCE LAYER (Database)          │
│  └─ SQLite Operations                  │
└─────────────────────────────────────────┘
```

---

## 1. Sales Processing (`modules/sales.py`)

Handles all transaction-related operations including cart management and checkout.

### Core Responsibilities

- **Cart Management** - Add/remove items, update quantities
- **Transaction Validation** - Check stock, payment amounts
- **Sale Recording** - Persist sales to database
- **Inventory Updates** - Deduct stock from inventory
- **Receipt Generation** - Format transaction records

### Key Functions

#### Cart Operations

```python
def cart_add_item(cart: list, product: dict, quantity: int = 1) -> Tuple[list, bool, str]:
    """
    Business Logic:
    1. Validate quantity > 0
    2. Check available stock (including items already in cart)
    3. Check for duplicate items in cart
    4. Calculate subtotal (quantity * unit_price)
    5. Return updated cart or error
    
    Returns:
        (updated_cart, success, message)
    
    Example:
        cart = []
        product = {'product_id': 1, 'product_name': 'Laptop', 'price': 999.99, 'stock': 10}
        cart, ok, msg = cart_add_item(cart, product, 2)
        # Result: cart = [{'product_id': 1, 'product_name': 'Laptop', 'unit_price': 999.99, 
        #                   'quantity': 2, 'subtotal': 1999.98}]
    """
```

#### Cart Calculations

```python
def cart_totals(cart: list, discount: float = 0.0, tax_rate: float = 0.0) -> dict:
    """
    Business Logic:
    1. Sum all item subtotals -> subtotal
    2. Cap discount (can't exceed subtotal)
    3. Calculate after-discount amount
    4. Calculate tax on after-discount amount
    5. Calculate grand total
    
    Returns:
        {
            'subtotal': float,      # Sum of all item subtotals
            'discount': float,      # Applied discount
            'tax': float,          # Calculated tax
            'total': float         # Final amount due
        }
    
    Example:
        cart = [{'subtotal': 1999.98}, {'subtotal': 49.99}]  # 2 items
        totals = cart_totals(cart, discount=50.00, tax_rate=0.15)
        # subtotal: 2049.97
        # discount: 50.00
        # after:    1999.97
        # tax:      299.99  (1999.97 * 0.15)
        # total:    2299.96
    """
```

#### Checkout & Sale Processing

```python
def process_sale(cart: list, user_id: int, payment_method: str, amount_paid: float,
                 discount: float = 0.0, tax_rate: float = 0.0, customer_id: int = None) -> Tuple[bool, Optional[int], float, str]:
    """
    Business Logic Flow:
    1. Validate cart is not empty
    2. Validate payment_method in ('cash', 'momo', 'card')
    3. Calculate totals using cart_totals()
    4. Validate amount_paid >= total (no short payments)
    5. BEGIN TRANSACTION:
       a. INSERT INTO sales (transaction record)
       b. INSERT INTO sale_items (one per cart item)
       c. INSERT INTO payments (payment record)
       d. FOR EACH item: UPDATE inventory (deduct stock)
       e. INSERT INTO inventory_transactions (audit trail)
    6. COMMIT transaction
    7. Calculate and return change
    
    Returns:
        (success: bool, sale_id: int or None, change: float, message: str)
    
    Database Changes:
        - Creates sale record
        - Creates sale_item records (one per product)
        - Creates payment record
        - Updates inventory quantities
        - Creates inventory_transaction records for audit
    
    Example:
        success, sale_id, change, msg = process_sale(
            cart=[{'product_id': 1, 'quantity': 2, 'unit_price': 100, 'subtotal': 200}],
            user_id=5,
            payment_method='cash',
            amount_paid=250.00,
            discount=0,
            tax_rate=0.0
        )
        # Result:
        # success = True
        # sale_id = 42
        # change = 50.00
        # msg = "Sale completed successfully."
    """
```

#### Sale Retrieval

```python
def get_sale_details(sale_id: int) -> dict:
    """
    Business Logic:
    1. Query sales table for transaction
    2. Query sale_items table for products
    3. Query payments table for payment details
    4. Join with users for cashier name
    5. Join with customers if applicable
    6. Return complete transaction with line items
    
    Returns:
        {
            'sale_id': int,
            'sale_date': str (ISO format),
            'total_amount': float,
            'discount': float,
            'tax': float,
            'payment_method': str,
            'cashier': str,
            'customer': str or None,
            'amount_paid': float,
            'change_given': float,
            'items': [
                {
                    'product_name': str,
                    'quantity': int,
                    'unit_price': float,
                    'subtotal': float
                }
            ]
        }
    """
```

#### Receipt Generation

```python
def generate_receipt(sale_id: int, store_name: str = "POS System") -> str:
    """
    Business Logic:
    1. Get sale details
    2. Format as receipt string with:
       - Header (store name)
       - Receipt number and date
       - Cashier name
       - Each line item with qty, price, total
       - Subtotal, discount, tax, grand total
       - Payment method and change
       - Footer message
    
    Returns:
        Formatted receipt as multi-line string
    
    Example Output:
        ========================================
                    POS System
        ========================================
        Receipt #: 42
        Date: 2024-01-15 14:30:00
        Cashier: John Doe
        ----------------------------------------
        Item                Qty Price   Total
        ----------------------------------------
        Laptop               1   999.99  999.99
        Mouse                2    29.99   59.98
        ----------------------------------------
        Subtotal:                      1059.97
        Discount:                         0.00
        Tax (0%):                         0.00
        Total:                         1059.97
        Amount Paid:                   1500.00
        Change:                         440.03
        ----------------------------------------
        Payment Method:                  CASH
        ========================================
        Thank you for your purchase!
        Please come again!
    """
```

### Business Rules

1. **Stock Validation**
   - Cannot add more items to cart than available
   - Must account for items already in cart when checking

2. **Discount Rules**
   - Discount cannot exceed subtotal
   - Discount is applied before tax calculation

3. **Tax Calculation**
   - Tax is calculated on after-discount amount
   - Can be 0 (no tax) or percentage-based

4. **Payment Validation**
   - Only cash, momo, or card allowed
   - Amount paid must be >= total
   - Calculates change accurately to 2 decimals

5. **Transaction Integrity**
   - All sale operations in single transaction
   - Inventory deduction happens atomically with sale
   - Rollback on any error

---

## 2. Inventory Control (`modules/products.py` + inventory functions)

Manages product availability and stock levels.

### Core Responsibilities

- **Product Catalog** - Maintain product master data
- **Stock Tracking** - Monitor current quantities
- **Low Stock Detection** - Alert when below threshold
- **Inventory Updates** - Add/remove from inventory
- **Audit Trail** - Log all inventory changes

### Key Functions

#### Product Retrieval

```python
def get_all_products(include_inactive: bool = False) -> List[Dict]:
    """
    Business Logic:
    1. Query products table
    2. JOIN with inventory for stock levels
    3. Optionally filter out inactive products (is_active = 0)
    4. Calculate low_stock_alert flag
    
    Returns:
        [
            {
                'product_id': int,
                'product_name': str,
                'category': str,
                'price': float,
                'barcode': str or None,
                'supplier': str,
                'stock': int,
                'low_stock_alert': int (threshold),
                'is_active': int (1 or 0)
            }
        ]
    """
```

#### Product Search

```python
def search_products(keyword: str) -> List[Dict]:
    """
    Business Logic:
    1. Search product_name LIKE keyword
    2. OR search category LIKE keyword
    3. OR search barcode LIKE keyword
    4. Only return active products
    5. Include inventory levels
    
    Returns:
        List of matching products with inventory
    """

def get_product_by_barcode(barcode: str) -> Optional[Dict]:
    """
    Business Logic:
    1. Validate barcode not empty
    2. Query by barcode (POS scanning use case)
    3. Return with current inventory
    4. Used for quick checkout
    """

def get_product_by_id(product_id: int) -> Optional[Dict]:
    """
    Business Logic:
    1. Query product by ID
    2. Include inventory details
    3. Return None if not found or inactive
    """
```

#### Product Management

```python
def add_product(product_name: str, category: str, price: float,
                barcode: str = None, supplier: str = None,
                initial_stock: int = 0, low_stock_alert: int = 5,
                user_id: int = None) -> Tuple[bool, str]:
    """
    Business Logic:
    1. Validate required fields (name, category, price)
    2. Check price >= 0
    3. Check initial_stock >= 0
    4. Check low_stock_alert >= 0
    5. Check barcode uniqueness (if provided)
    6. BEGIN TRANSACTION:
       a. INSERT INTO products
       b. INSERT INTO inventory with initial_stock
       c. If initial_stock > 0: INSERT INTO inventory_transactions
    7. COMMIT
    
    Validation Rules:
        - product_name: not empty
        - price: must be >= 0
        - initial_stock: must be >= 0
        - low_stock_alert: must be >= 0
        - barcode: must be unique (if provided)
    
    Returns:
        (success, message)
    """

def update_product(product_id: int, product_name: str = None,
                   category: str = None, price: float = None,
                   barcode: str = None, supplier: str = None,
                   low_stock_alert: int = None, user_id: int = None) -> Tuple[bool, str]:
    """
    Business Logic:
    1. Build UPDATE query from provided fields
    2. Validate each provided field
    3. If low_stock_alert provided: update inventory record separately
    4. If barcode provided: check uniqueness
    
    Returns:
        (success, message)
    """

def delete_product(product_id: int) -> Tuple[bool, str]:
    """
    Business Logic (Soft Delete):
    1. Check if product has sales records
    2. If YES: set is_active = 0 (soft delete, preserve history)
    3. If NO: hard delete both product and inventory records
    
    This protects data integrity for reporting.
    """
```

#### Stock Level Management

```python
def get_low_stock_products() -> List[Dict]:
    """
    Business Logic:
    1. Query all products
    2. Filter WHERE quantity <= low_stock_alert
    3. Sort by urgency (lowest stock first)
    
    Returns:
        Products needing reorder
    
    Business Use:
        - Manager dashboard alert
        - Reorder trigger
    """

def adjust_stock(product_id: int, quantity_change: int,
                 reason: str = "Manual adjustment",
                 user_id: int = None) -> Tuple[bool, int]:
    """
    Business Logic:
    1. Get current quantity from inventory
    2. Calculate new_qty = current + quantity_change
    3. Validate new_qty >= 0 (no negative inventory)
    4. BEGIN TRANSACTION:
       a. UPDATE inventory SET quantity = new_qty
       b. INSERT INTO inventory_transactions (audit record)
    5. COMMIT
    6. Return updated quantity
    
    Parameters:
        quantity_change: positive (add) or negative (remove)
        reason: description of adjustment (e.g., "Damage", "Inventory Count")
    
    Returns:
        (success, new_quantity) or (False, error_message)
    """
```

### Business Rules

1. **Product Validation**
   - Name cannot be empty
   - Price must be >= 0
   - Stock cannot be negative
   - Barcode must be unique

2. **Stock Rules**
   - Never allow negative inventory
   - Low stock alerts at configurable threshold
   - Loss-of-stock prevents sales

3. **Data Integrity**
   - Never hard-delete if sales history exists
   - Always log inventory changes
   - Maintain audit trail for compliance

4. **Categories**
   - Product categorization for filtering
   - Default category: "General"

---

## 3. Payment Handling (`modules/sales.py` + payment logic)

Processes and records payment transactions.

### Core Responsibilities

- **Payment Validation** - Verify sufficient payment received
- **Multiple Methods** - Cash, Mobile Money (momo), Card
- **Change Calculation** - Accurate to cents/smallest unit
- **Payment Recording** - Persist payment details
- **Reconciliation** - Track cash vs electronic payments

### Key Functions

#### Payment Processing

```python
def process_payment(sale_total: float, amount_paid: float,
                   payment_method: str) -> Tuple[bool, float, str]:
    """
    Business Logic:
    1. Validate payment_method in ('cash', 'momo', 'card')
    2. Validate amount_paid >= sale_total (no short payment)
    3. Calculate change = amount_paid - sale_total
    4. Round change to nearest cent (2 decimals)
    5. Return with validation status
    
    Returns:
        (success: bool, change: float, message: str)
    
    Validation Rules:
        - payment_method must be valid
        - amount_paid must be numeric and >= 0
        - amount_paid must be >= sale_total
    
    Example:
        success, change, msg = process_payment(
            sale_total=1523.47,
            amount_paid=1600.00,
            payment_method='cash'
        )
        # Result:
        # success = True
        # change = 76.53
        # msg = "Payment accepted"
    """
```

#### Payment Recording

```python
def record_payment(sale_id: int, amount_paid: float,
                   change_given: float, payment_method: str) -> bool:
    """
    Business Logic:
    1. Create payment record in database
    2. Link to sale via sale_id
    3. Record timestamp
    4. Store payment method for reporting
    
    Database:
        INSERT INTO payments (sale_id, amount_paid, change_given, payment_method)
    
    Returns:
        Success status
    """
```

#### Payment Method Analytics

```python
def get_payment_method_breakdown(start_date: str, end_date: str) -> List[Dict]:
    """
    Business Logic:
    1. Group sales by payment_method
    2. Sum transactions per method
    3. Sum revenue per method
    4. Calculate percentage of total
    5. Calculate average transaction value per method
    
    Returns:
        [
            {
                'payment_method': str,           # 'cash', 'momo', 'card'
                'transactions': int,             # count
                'revenue': float,                # total amount
                'percentage': float,             # % of total revenue
                'avg_transaction_value': float   # average per transaction
            }
        ]
    
    Business Use:
        - Cash flow analysis
        - Electronic vs cash comparison
        - Trend identification
    """
```

### Business Rules

1. **Validation**
   - Only accept: cash, momo, card
   - Amount paid must be >= total
   - Change must be non-negative

2. **Precision**
   - Calculate change to nearest cent (2 decimals)
   - No rounding errors
   - Handle edge cases (e.g., $100 - $99.99 = $0.01)

3. **Recording**
   - All payments logged with method
   - Change given tracked
   - Timestamp recorded

4. **Security**
   - No modification after recording
   - Audit trail maintained

---

## 4. Report Generation (`modules/reports.py`)

Generates business analytics and performance reports.

### Core Responsibilities

- **Sales Analytics** - Revenue, transactions, trends
- **Product Analytics** - Top sellers, low performers
- **Performance Metrics** - Cashier productivity, payment methods
- **Inventory Reporting** - Stock levels, turnover
- **Trend Analysis** - Daily/range comparisons

### Key Functions

#### Daily Reporting

```python
def get_daily_summary(date: str = None) -> Dict:
    """
    Business Logic:
    1. Query sales for specified date
    2. SUM(total_amount) -> total_revenue
    3. COUNT(*) -> total_transactions
    4. AVG(total_amount) -> average_transaction
    5. SUM(discount) -> total_discounts
    6. SUM(tax) -> total_tax
    7. MAX/MIN(total_amount) -> max/min sales
    
    Returns:
        {
            'total_transactions': int,
            'total_revenue': float,
            'total_discounts': float,
            'total_tax': float,
            'avg_sale_value': float,
            'max_sale_value': float,
            'min_sale_value': float,
            'net_revenue': float  # revenue - discounts
        }
    
    Business Use:
        - End-of-day summary
        - Manager dashboard
        - Performance tracking
    """

def get_sales_by_date_range(start_date: str, end_date: str) -> List[Dict]:
    """
    Business Logic:
    1. Group sales by DATE(sale_date)
    2. For each day: calculate totals
    3. Sort chronologically
    4. Return daily summaries
    
    Returns:
        [
            {
                'sale_date': str,
                'total_transactions': int,
                'total_revenue': float,
                'total_discounts': float,
                'total_tax': float
            }
        ]
    
    Business Use:
        - Weekly/monthly trends
        - Performance comparison
        - Revenue projection
    """
```

#### Product Analytics

```python
def get_top_products(limit: int = 10, start_date: str = None,
                     end_date: str = None) -> List[Dict]:
    """
    Business Logic:
    1. Join sale_items with products
    2. GROUP BY product
    3. SUM(quantity) -> units_sold
    4. SUM(subtotal) -> revenue
    5. Calculate contribution_percentage
    6. ORDER BY units_sold DESC
    7. LIMIT to top N
    
    Returns:
        [
            {
                'product_id': int,
                'product_name': str,
                'category': str,
                'units_sold': int,
                'revenue': float,
                'avg_price': float,
                'contribution_percentage': float  # % of total revenue
            }
        ]
    
    Business Use:
        - Identify bestsellers
        - Stock replenishment priority
        - Marketing focus
    """

def get_low_performing_products(limit: int = 10,
                                days: int = 30) -> List[Dict]:
    """
    Business Logic:
    1. Query products with minimal sales in last N days
    2. Include current stock level
    3. Identify slow-moving inventory
    
    Returns:
        Products with low sales volume
    
    Business Use:
        - Identify obsolete items
        - Clearance decisions
        - Stock optimization
    """
```

#### Performance Reporting

```python
def get_cashier_performance(start_date: str = None,
                           end_date: str = None) -> List[Dict]:
    """
    Business Logic:
    1. Group sales by user_id (cashier)
    2. For each cashier:
       - COUNT(sale_id) -> transactions
       - SUM(total_amount) -> revenue
       - AVG(total_amount) -> avg_value
       - SUM(discount) -> total_discounts
       - COUNT(DISTINCT customer_id) -> unique_customers
    3. ORDER BY revenue DESC
    
    Returns:
        [
            {
                'user_id': int,
                'cashier': str,           # full name
                'role': str,
                'transactions': int,      # count
                'revenue': float,         # total amount
                'avg_sale_value': float,  # average transaction
                'total_discounts': float, # discounts given
                'unique_customers': int   # unique customers served
            }
        ]
    
    Business Use:
        - Performance review
        - Incentive calculation
        - Training identification
    """

def get_payment_method_breakdown(start_date: str = None,
                                 end_date: str = None) -> List[Dict]:
    """
    Business Logic:
    1. GROUP BY payment_method
    2. For each method:
       - COUNT(*) -> transactions
       - SUM(total_amount) -> revenue
       - AVG(total_amount) -> avg_value
       - Calculate percentage of total
    3. ORDER BY revenue DESC
    
    Returns:
        [
            {
                'payment_method': str,           # 'cash', 'momo', 'card'
                'transactions': int,
                'revenue': float,
                'avg_transaction_value': float,
                'percentage': float   # % of total sales
            }
        ]
    
    Business Use:
        - Cash flow analysis
        - Payment trend analysis
        - Infrastructure planning
    """
```

#### Inventory Reporting

```python
def get_inventory_report() -> List[Dict]:
    """
    Business Logic:
    1. Query all active products with inventory
    2. Calculate flags:
       - out_of_stock: quantity = 0
       - low_stock: quantity <= low_stock_alert
       - healthy: quantity > low_stock_alert
    3. Sort by urgency (out_of_stock, then low, then quantity)
    
    Returns:
        [
            {
                'product_id': int,
                'product_name': str,
                'category': str,
                'quantity': int,
                'low_stock_alert': int,
                'price': float,
                'status': str,  # 'in_stock', 'low_stock', 'out_of_stock'
                'value': float  # quantity * price (inventory value)
            }
        ]
    
    Business Use:
        - Inventory valuation
        - Reorder management
        - Physical count reconciliation
    """
```

### Business Rules

1. **Calculation Accuracy**
   - All financial calculations to 2 decimals
   - Percentage calculations to 1-2 decimals
   - No rounding errors

2. **Data Aggregation**
   - Always include date ranges
   - Handle zero-transaction days
   - Default to today if no date specified

3. **Performance Metrics**
   - Compare periods consistently
   - Identify trends vs anomalies
   - Account for seasonal variations

4. **Data Integrity**
   - Only include complete transactions
   - Exclude voided/cancelled sales
   - Maintain referential integrity

---

## Data Flow: Complete Sale Example

### Step 1: Customer Adds Items to Cart
```python
# Service layer validates and coordinates
sales_svc.add_to_cart(cart, product, 2)
  ├─ ProductService confirms stock available
  └─ cart_add_item() (business logic)
    ├─ Validate quantity > 0
    ├─ Check available stock
    ├─ Calculate subtotal
    └─ Return updated cart
```

### Step 2: Customer Enters Payment
```python
# Service calculates totals
totals = sales_svc.get_cart_totals(cart, discount=50, tax_rate=0.0)
  └─ cart_totals() (business logic)
    ├─ Sum all subtotals
    ├─ Cap discount
    ├─ Calculate tax
    └─ Return totals dict
```

### Step 3: Checkout Processing
```python
# Service orchestrates sale
success, sale_id, change, msg = sales_svc.checkout(
    cart, payment_method='cash', amount_paid=1500.00
)
  └─ process_sale() (business logic)
    ├─ Validate cart not empty
    ├─ Validate payment method
    ├─ Calculate totals
    ├─ BEGIN TRANSACTION
    │  ├─ INSERT sale record
    │  ├─ INSERT sale_items (per product)
    │  ├─ INSERT payment record
    │  ├─ UPDATE inventory quantities
    │  └─ INSERT inventory_transactions
    ├─ COMMIT
    └─ Return (True, sale_id, change, msg)
```

### Step 4: Receipt Generation
```python
# Service generates receipt
receipt = sales_svc.get_receipt(sale_id)
  └─ generate_receipt() (business logic)
    ├─ Get sale details with items
    ├─ Format receipt string
    ├─ Include all transaction details
    └─ Return formatted receipt
```

### Step 5: Reporting
```python
# Service provides analytics
daily = ReportService().get_daily_summary()
  └─ get_daily_summary() (business logic)
    ├─ Query sales for date
    ├─ Aggregate revenue
    ├─ Calculate metrics
    └─ Return summary dict
```

---

## Database Tables Used

### Sales Domain
```sql
sales                 -- Transaction header
sale_items           -- Line items per sale
payments             -- Payment details
inventory_transactions -- Audit trail
```

### Product Domain
```sql
products             -- Product master
inventory            -- Stock levels
categories           -- Product categories
```

### User Domain
```sql
users                -- Cashiers and staff
```

---

## Error Handling

All business logic functions follow consistent error patterns:

```python
def operation(...) -> Tuple[bool, Optional[Result], str]:
    """
    Returns:
        (success: bool, result: Optional[result_data], message: str)
    
    On error:
        return False, None, "Error description"
    
    On success:
        return True, result_data, "Success message"
    """
```

---

## Performance Considerations

1. **Database Queries**
   - Use indexes: barcode, category, sale_date, user_id
   - Batch inserts for sale_items
   - Aggregate queries for reports

2. **Caching**
   - Customer lookup
   - Product categories
   - User list (small, static)

3. **Transaction Size**
   - Keep transactions small (single sale)
   - Avoid long-running transactions
   - Log changes for audit

---

## Testing the Business Logic

```python
from modules.sales import cart_add_item, process_sale, cart_totals
from modules.products import get_all_products, add_product, adjust_stock

# Test cart operations
cart = []
product = {'product_id': 1, 'product_name': 'Laptop', 'price': 999.99, 'stock': 10}
cart, ok, msg = cart_add_item(cart, product, 2)
assert ok and len(cart) == 1

# Test price calculation
totals = cart_totals(cart, discount=100, tax_rate=0.15)
assert totals['total'] > 0

# Test sale processing
success, sale_id, change, msg = process_sale(
    cart=cart,
    user_id=1,
    payment_method='cash',
    amount_paid=2500.00,
    discount=100,
    tax_rate=0.15
)
assert success and sale_id is not None
```

---

## Summary

The Application Layer implements pure business logic without any UI concerns:

| Component | Purpose | Key Functions |
|-----------|---------|---------------|
| **Sales Processing** | Transaction handling | cart_add_item, process_sale, generate_receipt |
| **Inventory Control** | Stock management | adjust_stock, get_low_stock_products, add_product |
| **Payment Handling** | Payment validation | process_payment, record_payment, payment_breakdown |
| **Report Generation** | Business analytics | get_daily_summary, get_top_products, get_cashier_performance |

All functions maintain:
- ✓ Data integrity (transactions)
- ✓ Business rule validation
- ✓ Audit trail logging
- ✓ Error handling
- ✓ UI independence
