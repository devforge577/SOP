# Quick Start: Using the Services Layer

The new **Services Layer** is **optional and non-breaking**. You can gradually migrate existing code without any disruption.

## Existing Code (Still Works ✓)

```python
# Direct module usage - no changes needed
from modules.products import get_all_products, add_product
from modules.sales import cart_add_item, process_sale
from modules.auth import login

products = get_all_products()
success, msg = add_product("Laptop", "Electronics", 999.99)
```

## New Service-Based Code (Recommended)

```python
# Service layer usage - cleaner, permission-checked
from services import AuthService, ProductService, SalesService

# Initialize services
auth_svc = AuthService()
success, user, msg = auth_svc.authenticate("cashier", "cashier123")

if success:
    # Services are permission-aware
    product_svc = ProductService(auth_svc)
    sales_svc = SalesService(auth_svc, product_svc)
    
    # All operations automatically check permissions
    products = product_svc.get_all_products()
    
    # Permission-protected operations fail gracefully
    ok, message = product_svc.add_product(...)  # Denied for cashiers
```

---

## Architecture Layers (Reference)

```
┌─────────────────────────────────────────┐
│  PRESENTATION (views/)                  │
│  ├─ login_view.py                       │
│  ├─ cashier_view.py                     │
│  ├─ product_view.py                     │
│  └─ reports_view.py                     │
└──────────────┬──────────────────────────┘
               │ Uses
        ┌──────▼──────────┐
        │  SERVICES (NEW) │ ← Add this layer
        │ (services/)     │   gradually to views
        └──────┬──────────┘
               │ Uses
┌──────────────▼──────────────────────────┐
│  BUSINESS LOGIC (modules/)              │
│  ├─ auth.py                             │
│  ├─ products.py                         │
│  ├─ sales.py                            │
│  └─ reports.py                          │
└──────────────┬──────────────────────────┘
               │ Uses
┌──────────────▼──────────────────────────┐
│  DATABASE (database/)                   │
│  └─ db.py                               │
└──────────────┬──────────────────────────┘
               │ Uses
┌──────────────▼──────────────────────────┐
│  DATA (SQLite)                          │
│  └─ pos_system.db                       │
└─────────────────────────────────────────┘
```

---

## Service Classes Overview

### AuthService
**Location:** `services/auth_service.py`

```python
from services import AuthService

auth = AuthService()

# Authenticate
success, user, msg = auth.authenticate("admin", "admin123")
if success:
    print(f"Logged in as {user['full_name']}")

# Check permissions
if auth.user_has_permission('manage_products'):
    # Show admin features
    
# Check role
if auth.has_role('admin'):
    # Show admin-only features
    
# Logout
auth.logout()
```

---

### ProductService
**Location:** `services/product_service.py`

```python
from services import ProductService

products = ProductService(auth_service=auth)

# Read operations (no permission check needed)
all = products.get_all_products()
found = products.search_products("laptop")
product = products.get_product_by_id(42)
product = products.get_product_by_barcode("BAR001")
categories = products.get_categories()
low_stock = products.get_low_stock_products()

# Write operations (permission-checked)
success, msg = products.add_product(
    product_name="USB Cable",
    category="Electronics",
    price=9.99,
    barcode="BAR123",
    supplier="CableCorp",
    initial_stock=100,
    low_stock_alert=20
)

success, msg = products.update_product(
    product_id=42,
    price=8.99,
    category="Accessories"
)

success, msg = products.delete_product(product_id=42)
```

---

### SalesService
**Location:** `services/sales_service.py`

```python
from services import SalesService

sales = SalesService(auth_service=auth, product_service=products)

# Cart operations
cart = sales.create_cart()

# Add to cart
cart, ok, msg = sales.add_to_cart(
    cart,
    product={'product_id': 1, 'product_name': 'Laptop', 'price': 999.99, 'stock': 10},
    quantity=1
)

# Update quantity
cart, ok, msg = sales.update_cart_quantity(cart, product_id=1, new_qty=2)

# Remove from cart
cart = sales.remove_from_cart(cart, product_id=1)

# Calculate totals
totals = sales.get_cart_totals(cart, discount=10.00, tax_rate=0.0)
print(f"Total: ${totals['total']:.2f}")

# Get cart summary
summary = sales.get_cart_summary(cart)
print(f"{summary['item_count']} items, ${summary['total_value']:.2f}")

# Process payment
success, sale_id, change, msg = sales.checkout(
    cart=cart,
    payment_method="cash",
    amount_paid=1500.00,
    discount=0,
    tax_rate=0.0
)

if success:
    receipt = sales.get_receipt(sale_id)
    print(receipt)
```

---

### ReportService
**Location:** `services/report_service.py`

```python
from services import ReportService

reports = ReportService(auth_service=auth)

# Get daily summary
today = reports.get_daily_summary()  # Uses today's date
print(f"Revenue: ${today['total_revenue']:.2f}")

# Get monthly sales
sales = reports.get_sales_range("2024-01-01", "2024-01-31")
for day in sales:
    print(f"{day['sale_date']}: ${day['total_revenue']:.2f}")

# Top products
top10 = reports.get_top_products(limit=10)
for product in top10:
    print(f"{product['product_name']}: {product['units_sold']} units")

# Payment method breakdown
methods = reports.get_payment_breakdown("2024-01-01", "2024-01-31")
for method in methods:
    print(f"{method['payment_method']}: {method['percentage']}%")

# Cashier performance
cashiers = reports.get_cashier_performance("2024-01-01", "2024-01-31")
for cashier in cashiers:
    print(f"{cashier['cashier_name']}: {cashier['transactions']} sales")

# Inventory
inventory = reports.get_inventory_status()

# Recent activity
recent = reports.get_recent_activity(limit=20)
```

---

## Gradual Migration Strategy

### Step 1: Use Services in New Features
When adding new functionality, use services from the start.

### Step 2: Update One View at a Time
Migrate existing views gradually:

```python
# Before
from modules.products import get_all_products
def _load_products(self):
    self.products = get_all_products()

# After
from services import ProductService
def __init__(self, auth_service):
    self.product_svc = ProductService(auth_service)
def _load_products(self):
    self.products = self.product_svc.get_all_products()
```

### Step 3: Complete Migration Path

1. **Phase 1:** Services created (DONE ✓)
2. **Phase 2:** Update `main.py` to initialize services
3. **Phase 3:** Migrate views one at a time
4. **Phase 4:** Remove direct module imports from views
5. **Phase 5:** Add unit tests for services

---

## Permission Enforcement Example

### Before (No Permission Checking)
```python
# Anyone can call this regardless of role
success, msg = add_product("Hacker Item", "Bad", 1000)
```

### After (Permission-Checked)
```python
# Only manager/admin can call this
product_svc = ProductService(auth_service=auth)

# If cashier calls this:
success, msg = product_svc.add_product("Item", "Category", 100)
# Returns: (False, "Insufficient permissions to add products")

# If manager calls this:
success, msg = product_svc.add_product("Item", "Category", 100)
# Returns: (True, "Product added successfully (ID: 42)")
```

---

## Testing the Services Layer

```python
from services import AuthService, ProductService, SalesService

# Test with admin
auth = AuthService()
auth.authenticate("admin", "admin123")
assert auth.user_has_permission('manage_products')  # True

products = ProductService(auth)
success, msg = products.add_product("Test", "Test", 99.99)
assert success  # True

# Test with cashier
auth.logout()
auth.authenticate("cashier", "cashier123")
assert not auth.user_has_permission('manage_products')  # False

success, msg = products.add_product("Test", "Test", 99.99)
assert not success  # False - permission denied
assert "Insufficient permissions" in msg
```

---

## No Breaking Changes ✓

The new services layer is **completely optional**:

- ✓ All existing code continues to work
- ✓ Views can use modules directly OR services
- ✓ No modifications needed to business logic
- ✓ No database schema changes
- ✓ Can mix old and new code during migration

---

## Summary

| Aspect | Without Services | With Services |
|--------|------------------|---------------|
| Permission Check | Manual in each view | Automatic |
| Code Reuse | Low (duplicated checks) | High |
| Testing | Harder (mixed concerns) | Easier (isolated) |
| Maintainability | Harder (tight coupling) | Easy (clean separation) |
| Scalability | Limited | Excellent |
| Migration | N/A | Gradual |

**Recommendation:** Use services for all new code, migrate existing views gradually.
