# SOP POS System - Documentation Index

Complete reference for the Point-of-Sale system architecture, implementation, and usage.

---

## Quick Navigation

### Core Documentation Files

| File | Purpose | Audience | Length |
|------|---------|----------|--------|
| **ARCHITECTURE.md** | System layered design, data flows, permission model | Architects, Senior Devs | ~400 lines |
| **APPLICATION_LAYER.md** | Business logic implementation details | Backend Devs | ~500 lines |
| **APPLICATION_LAYER_REFERENCE.md** | Code examples and integration patterns | Developers | ~600 lines |
| **PRESENTATION_LAYER.md** | UI components and design patterns | Frontend Devs | ~350 lines |
| **SERVICES_QUICK_START.md** | Service layer usage guide | Developers | ~300 lines |

---

## Documentation Structure

```
SOP/
├── DOCUMENTATION_INDEX.md          (This file)
│
├── ARCHITECTURE.md                 (Design & Data Flow)
│   ├── Layered Architecture (5 layers)
│   ├── Data Flow Diagrams
│   ├── Permission Model
│   ├── Database Schema Overview
│   ├── Dependency Mapping
│   └── Migration Strategy
│
├── APPLICATION_LAYER.md            (Business Logic)
│   ├── Sales Processing Functions
│   ├── Inventory Management
│   ├── Payment Handling
│   ├── Report Generation Functions
│   └── Validation Rules & Error Handling
│
├── APPLICATION_LAYER_REFERENCE.md  (Examples & Integration)
│   ├── Sales Module (with code examples)
│   ├── Inventory Module (with code examples)
│   ├── Payment Flow (with code examples)
│   ├── Report Generation (with code examples)
│   ├── Complete Workflow Example
│   ├── Error Handling Patterns
│   ├── Unit Test Examples
│   └── Integration Summary Table
│
├── PRESENTATION_LAYER.md           (User Interface)
│   ├── Login Component
│   ├── Cashier Screen
│   ├── Product Management
│   ├── Reports Dashboard
│   ├── Data Contracts (Request/Response)
│   └── Design Patterns
│
└── SERVICES_QUICK_START.md         (Service Layer API)
    ├── AuthService Usage
    ├── ProductService Usage
    ├── SalesService Usage
    ├── ReportService Usage
    └── Permission Checking Pattern
```

---

## 1. Getting Started

### For New Team Members

**Start here if you're new to the project:**

1. Read: [ARCHITECTURE.md](ARCHITECTURE.md) - Understand the big picture (15 min read)
2. Read: [PRESENTATION_LAYER.md](PRESENTATION_LAYER.md) - See what users interact with (15 min read)
3. Read: [APPLICATION_LAYER.md](APPLICATION_LAYER.md) - Learn the business logic (20 min read)
4. Reference: [APPLICATION_LAYER_REFERENCE.md](APPLICATION_LAYER_REFERENCE.md) - Code examples (as needed)

**For Service Layer Developers:**

1. Read: [SERVICES_QUICK_START.md](SERVICES_QUICK_START.md) - Service API reference (10 min read)
2. Skim: [ARCHITECTURE.md](ARCHITECTURE.md#data-flow) - Data flow section
3. Reference: [APPLICATION_LAYER_REFERENCE.md](APPLICATION_LAYER_REFERENCE.md#integration-example) - Integration patterns

---

## 2. System Architecture Overview

### Five-Layer Architecture

```
┌─────────────────────────────────────────────────┐
│  PRESENTATION LAYER                             │
│  (UI - Tkinter Views)                           │
│  LoginView | CashierView | ProductView |        │
│  ReportsView                                    │
└────────────────────┬────────────────────────────┘
                     │ Uses
┌────────────────────▼────────────────────────────┐
│  SERVICES LAYER                                 │
│  (Application Coordination)                     │
│  AuthService | ProductService | SalesService   │
│  ReportService                                  │
└────────────────────┬────────────────────────────┘
                     │ Calls
┌────────────────────▼────────────────────────────┐
│  APPLICATION LAYER                              │
│  (Business Logic - Core Rules)                  │
│  modules/auth.py | modules/products.py          │
│  modules/sales.py | modules/reports.py          │
└────────────────────┬────────────────────────────┘
                     │ Uses
┌────────────────────▼────────────────────────────┐
│  PERSISTENCE LAYER                              │
│  (Database Access)                              │
│  database/db.py                                 │
└────────────────────┬────────────────────────────┘
                     │ Reads/Writes
┌────────────────────▼────────────────────────────┐
│  DATA LAYER                                     │
│  (SQLite Database)                              │
│  pos_system.db                                  │
└─────────────────────────────────────────────────┘
```

### Seeded Test Users

| Username | Password | Role | Permissions |
|----------|----------|------|------------|
| `admin` | `admin123` | Admin | All operations |
| `manager` | `manager123` | Manager | Inventory, Reports, Voiding |
| `cashier` | `cashier123` | Cashier | POS checkout |

---

## 3. Core Modules

### Business Logic (Application Layer)

#### **modules/auth.py**
- Login and authentication
- Role-based permissions
- Session management

```python
from modules.auth import Auth, login, has_permission

success, user, msg = login("cashier", "cashier123")
if success:
    print(f"Logged in: {user['full_name']} ({user['role']})")
```

#### **modules/products.py**
- Product catalog management
- Inventory control
- Stock alerts

```python
from modules.products import get_all_products, search_products, add_product

products = get_all_products()
results = search_products("laptop")
success, msg = add_product("Mouse", "Electronics", 29.99)
```

#### **modules/sales.py**
- Shopping cart management
- Transaction processing
- Receipt generation

```python
from modules.sales import cart_add_item, process_sale, generate_receipt

success, sale_id, change, msg = process_sale(cart, user_id=3, 
                                              payment_method='cash',
                                              amount_paid=1200)
receipt = generate_receipt(sale_id)
```

#### **modules/reports.py**
- Sales analytics
- Performance metrics
- Inventory reporting

```python
from modules.reports import get_daily_summary, get_top_products

daily = get_daily_summary()
top_10 = get_top_products(limit=10)
```

### Service Layer (Coordination)

#### **services/auth_service.py**
- User authentication with permission checks
- Session validation

#### **services/product_service.py**
- Product operations with permission enforcement
- Prevents cashier from adding/deleting products

#### **services/sales_service.py**
- Coordinates cart, checkout, payment
- Single transaction boundary

#### **services/report_service.py**
- Analytics with permission checks
- Manager-only access

---

## 4. Common Tasks

### Add a New User

```python
from modules.auth import Auth
from database.db import get_db_connection, hash_password

with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (username, password, full_name, role)
        VALUES (?, ?, ?, ?)
    """, ("john123", hash_password("secure_pass"), "John Doe", "cashier"))
```

### Process a Sale

```python
from modules.sales import cart_add_item, process_sale

cart = []
for product in user_products:
    cart, ok, msg = cart_add_item(cart, product, quantity=1)

success, sale_id, change, msg = process_sale(
    cart, user_id=3, payment_method='cash', amount_paid=1500
)
```

### Generate Daily Report

```python
from modules.reports import get_daily_summary, get_top_products

summary = get_daily_summary()
print(f"Revenue: ${summary['total_revenue']:.2f}")
print(f"Transactions: {summary['total_transactions']}")

top = get_top_products(limit=5)
for product in top:
    print(f"{product['product_name']}: {product['units_sold']} sold")
```

### Add Inventory

```python
from modules.products import adjust_stock

success, new_qty = adjust_stock(
    product_id=42,
    quantity_change=50,
    reason="Received delivery #2024-001",
    user_id=2  # Manager
)
```

---

## 5. Database Schema

### Core Tables

**users**
- user_id: PK
- username: UNIQUE
- password: Hashed
- role: admin|manager|cashier
- is_active

**products**
- product_id: PK
- product_name
- category
- price
- barcode: UNIQUE
- is_active

**inventory**
- inventory_id: PK
- product_id: FK
- quantity
- low_stock_alert

**sales**
- sale_id: PK
- user_id: FK
- customer_id: FK (optional)
- total_amount
- discount
- payment_method

**sale_items**
- sale_item_id: PK
- sale_id: FK
- product_id: FK
- quantity
- unit_price
- subtotal

**payments**
- payment_id: PK
- sale_id: FK
- amount_paid
- change_given
- payment_method

### Additional Tables
- **customers**: For loyalty program (future)
- **inventory_transactions**: Audit trail for stock changes

---

## 6. Development Guides

### Adding a New Feature

**Example: Add Loyalty Points**

1. **Database**: Add loyalty_points to customers table
2. **Business Logic** (modules/sales.py): Update process_sale() to award points
3. **Service Layer** (services/sales_service.py): Add permission checks if needed
4. **Presentation** (views/cashier_view.py): Display points earned
5. **Report** (modules/reports.py): Add loyalty metrics

### Testing Business Logic

```python
import pytest
from modules.sales import cart_add_item, process_sale
from modules.products import get_all_products

def test_checkout():
    products = get_all_products()
    cart = []
    
    product = {
        'product_id': products[0]['product_id'],
        'product_name': products[0]['product_name'],
        'price': products[0]['price'],
        'stock': products[0]['stock']
    }
    
    cart, ok, msg = cart_add_item(cart, product, quantity=1)
    assert ok
    
    success, sale_id, change, msg = process_sale(
        cart, user_id=3, payment_method='cash', amount_paid=500
    )
    assert success
    assert change > 0
```

### Adding a New Permission

1. Add permission constant to `modules/auth.py`
2. Update role permissions in `get_role_permissions()`
3. Check in service layer: `if not has_permission(...): raise PermissionError`

---

## 7. Troubleshooting

### Issue: "ImportError: cannot import name 'ProductManager'"
- **Cause**: main.py tries to import classes that don't exist
- **Solution**: Ensure wrapper classes exist in modules/__init__.py
- **See**: ARCHITECTURE.md → Migration Strategy

### Issue: "FOREIGN KEY constraint failed"
- **Cause**: Trying to insert with invalid user_id/customer_id
- **Solution**: Verify IDs exist in database first
- **Reference**: Check seeded users above

### Issue: "Low stock alert not working"
- **Cause**: low_stock_alert not set in inventory table
- **Solution**: Run: `UPDATE inventory SET low_stock_alert = 20 WHERE low_stock_alert = 0`

### Issue: "Sales not showing in reports"
- **Cause**: Report queries filtering by wrong date
- **Solution**: Verify sale_date in database matches date range query

---

## 8. Performance Considerations

### Database Indexes
✓ products(barcode) - For quick barcode lookups in POS
✓ products(category) - For category filtering
✓ sales(sale_date) - For daily/monthly reports
✓ sales(user_id) - For cashier performance
✓ inventory(quantity, low_stock_alert) - For low stock alerts

### Caching Opportunities
- Product catalog (load on startup, invalidate on add/update/delete)
- User permissions (cache per session)
- Daily summary (cache and invalidate at midnight)

### Optimization Tips
1. Use barcode instead of product name for POS searches
2. Cache role permissions after login
3. Batch inventory adjustments when possible
4. Use indexes for date range queries

---

## 9. API Reference Summary

### Auth Module
```python
login(username, password) -> (bool, user_dict, message)
has_permission(user_id, action) -> bool
get_role_permissions(role) -> dict
```

### Product Module
```python
get_all_products() -> [product_dict]
search_products(query) -> [product_dict]
get_low_stock_products() -> [product_dict]
add_product(...) -> (bool, message)
```

### Sales Module
```python
cart_add_item(cart, product, qty) -> (cart, bool, message)
process_sale(cart, user_id, payment_method, amount_paid) -> (bool, sale_id, change, msg)
generate_receipt(sale_id) -> receipt_string
```

### Reports Module
```python
get_daily_summary() -> summary_dict
get_top_products(limit) -> [product_dict]
get_payment_method_breakdown() -> [payment_dict]
```

### Service Module
```python
AuthService.authenticate(username, password) -> user or None
ProductService.add_with_permission(product_data, user_id) -> (bool, msg)
SalesService.checkout(cart, user_id, payment) -> (bool, sale_id, change, msg)
ReportService.daily_revenue(user_id) -> revenue_decimal
```

---

## 10. File Locations Reference

```
c:\Users\dauda\Desktop\websites\SOP\
├── main.py                          Main entry point
├── init_data.py                     Database initialization
├── _init_.py                        Package marker
│
├── database/
│   ├── __init__.py
│   └── db.py                        Database setup & schema
│
├── modules/                         Business Logic Layer
│   ├── __init__.py
│   ├── auth.py                      Authentication & permissions
│   ├── products.py                  Inventory management
│   ├── sales.py                     POS transactions
│   └── reports.py                   Analytics
│
├── services/                        Application Services Layer
│   ├── __init__.py
│   ├── auth_service.py              Auth coordination
│   ├── product_service.py           Product operations
│   ├── sales_service.py             Sales coordination
│   └── report_service.py            Report coordination
│
├── views/                           Presentation Layer
│   ├── __init__.py
│   ├── login_view.py                Login screen
│   ├── cashier_view.py              POS interface
│   ├── product_view.py              Inventory UI
│   └── reports_view.py              Analytics dashboard
│
└── utils/                           Utilities
    └── __init__.py

DOCUMENTATION:
├── ARCHITECTURE.md                  System design
├── APPLICATION_LAYER.md             Business logic docs
├── APPLICATION_LAYER_REFERENCE.md   Code examples
├── PRESENTATION_LAYER.md            UI component docs
├── SERVICES_QUICK_START.md          Service layer guide
└── DOCUMENTATION_INDEX.md           This file
```

---

## 11. How to Contribute

### Adding a New Report

1. Add function to `modules/reports.py`
2. Call aggregation functions from database
3. Add service method to `services/report_service.py` with permission check
4. Add UI to `views/reports_view.py`
5. Document in `APPLICATION_LAYER_REFERENCE.md`

### Adding a New Product Field

1. Add column to products table (database/db.py)
2. Update product_dict structure in modules/products.py
3. Update product form in views/product_view.py
4. Add to ProductService in services/product_service.py

### Bug Fix Process

1. Write failing test case
2. Fix code in applicable layer (modules/ or services/)
3. Run tests to verify
4. Update documentation if behavior changed
5. Commit with test coverage

---

## 12. Next Steps / Enhancement Roadmap

### Phase 1: Core Stabilization (Now)
- ✅ Basic POS functionality
- ✅ Three-role authentication
- ✅ Product management
- ✅ Sales processing
- ✅ Daily reports

### Phase 2: Service Layer (In Progress)
- ✅ Service layer implementation
- ✅ Permission enforcement
- ✅ Integration testing
- ⏳ View migration to use services

### Phase 3: Advanced Features
- ⏳ Customer loyalty program
- ⏳ Discount/coupon system
- ⏳ Advanced inventory forecasting
- ⏳ Multi-store support

### Phase 4: Integration
- ⏳ REST API layer
- ⏳ Mobile POS support
- ⏳ Cloud synchronization
- ⏳ Advanced analytics

---

## Questions?

Refer to the specific documentation:
- **Architecture questions** → [ARCHITECTURE.md](ARCHITECTURE.md)
- **Code examples** → [APPLICATION_LAYER_REFERENCE.md](APPLICATION_LAYER_REFERENCE.md)
- **UI/UX questions** → [PRESENTATION_LAYER.md](PRESENTATION_LAYER.md)
- **Service usage** → [SERVICES_QUICK_START.md](SERVICES_QUICK_START.md)
- **Business logic** → [APPLICATION_LAYER.md](APPLICATION_LAYER.md)

**Last Updated:** Phase 5 (Application Layer Documentation Complete)
**Status:** ✓ All business logic verified and working
