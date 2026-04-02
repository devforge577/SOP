# POS System Architecture

## Overview

This POS system follows a **Layered Architecture** pattern with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│             PRESENTATION LAYER (UI/Views)              │
│  (Cashier Screen, Admin Dashboard, Product Search)     │
└──────────────────┬──────────────────────────────────────┘
                   │ (Uses)
┌──────────────────▼──────────────────────────────────────┐
│         APPLICATION SERVICES LAYER                     │
│  (Coordinates business logic, enforces permissions)    │
│  ├─ AuthService      (Authentication & Sessions)      │
│  ├─ ProductService   (Product Operations)              │
│  ├─ SalesService     (Cart & Transactions)             │
│  └─ ReportService    (Analytics & Reporting)           │
└──────────────────┬──────────────────────────────────────┘
                   │ (Uses)
┌──────────────────▼──────────────────────────────────────┐
│        BUSINESS LOGIC LAYER (Domain Logic)             │
│  (Pure business rules, no UI dependencies)             │
│  ├─ modules/auth.py      (Auth functions)              │
│  ├─ modules/products.py  (Product logic)               │
│  ├─ modules/sales.py     (Sales operations)            │
│  └─ modules/reports.py   (Report calculations)         │
└──────────────────┬──────────────────────────────────────┘
                   │ (Uses)
┌──────────────────▼──────────────────────────────────────┐
│      PERSISTENCE LAYER (Data Access)                   │
│  database/db.py (Database connection & queries)        │
└──────────────────┬──────────────────────────────────────┘
                   │ (Uses)
┌──────────────────▼──────────────────────────────────────┐
│         DATA LAYER (SQLite Database)                   │
│  pos_system.db                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Architecture Layers

### 1. **Presentation Layer** (`views/`)

User-facing interfaces built with Tkinter:

- **`login_view.py`** - Authentication UI
  - User credential input
  - Login validation feedback
  - Session initiation
  
- **`cashier_view.py`** - Point of Sale (Cashier Screen)
  - Product search & browsing
  - Shopping cart management
  - Payment interface
  - Receipt printing
  
- **`product_view.py`** - Admin Dashboard (Product Management)
  - Product CRUD operations
  - Inventory management
  - Category management
  - Bulk import
  
- **`reports_view.py`** - Analytics & Reporting Dashboard
  - Daily summaries
  - Top products
  - Payment breakdowns
  - Cashier performance
  - Inventory status

### 2. **Application Services Layer** (`services/`)

High-level operations and business coordination:

#### **AuthService** (`auth_service.py`)
```python
# Responsibilities:
- User authentication
- Session management
- Permission checking
- Role-based access control

# Usage in Views:
auth_svc = AuthService()
success, user, msg = auth_svc.authenticate(username, password)
if auth_svc.user_has_permission('manage_products'):
    # Show product management UI
```

#### **ProductService** (`product_service.py`)
```python
# Responsibilities:
- Product retrieval & search
- Product creation/update/deletion
- Category management
- Stock level queries
- Permission-guarded operations

# Usage in Views:
product_svc = ProductService(auth_service=auth_svc)
products = product_svc.search_products("laptop")
success, msg = product_svc.add_product(...)
```

#### **SalesService** (`sales_service.py`)
```python
# Responsibilities:
- Cart operations
- Checkout processing
- Payment handling
- Receipt generation
- Transaction logging

# Usage in Cashier View:
sales_svc = SalesService(auth_svc, product_svc)
cart, ok, msg = sales_svc.add_to_cart(cart, product, qty)
success, sale_id, change, msg = sales_svc.checkout(...)
receipt = sales_svc.get_receipt(sale_id)
```

#### **ReportService** (`report_service.py`)
```python
# Responsibilities:
- Report generation
- Analytics calculations
- Performance metrics
- Permission-guarded reporting

# Usage in Reports View:
report_svc = ReportService(auth_service=auth_svc)
daily = report_svc.get_daily_summary(date)
top_products = report_svc.get_top_products(10)
cashier_perf = report_svc.get_cashier_performance()
```

### 3. **Business Logic Layer** (`modules/`)

Pure business rules without UI dependencies:

- **`auth.py`** - Authentication logic
  - User login validation
  - Password hashing
  - Permission definitions
  - User CRUD operations
  
- **`products.py`** - Product operations
  - Product search & retrieval
  - Inventory calculations
  - Low-stock detection
  - Barcode resolution
  
- **`sales.py`** - Sales transactions
  - Cart management algorithms
  - Pricing calculations
  - Stock deduction
  - Receipt formatting
  
- **`reports.py`** - Analytics & reporting
  - Daily/range summaries
  - Performance calculations
  - Top product rankings
  - Inventory analytics

### 4. **Persistence Layer** (`database/db.py`)

Database connection and query execution:

- Connection pooling
- Transaction management
- Query helpers (execute_query, execute_insert, execute_update)
- Schema initialization
- Data seeding

### 5. **Data Layer** (`pos_system.db`)

SQLite database with tables:
- `users` - User accounts & roles
- `products` - Product catalog
- `inventory` - Stock levels
- `sales` - Transaction records
- `sale_items` - Line items per sale
- `customers` - Customer profiles
- `payments` - Payment details

---

## Data Flow Patterns

### Authentication Flow
```
LoginView (UI)
  ↓ (user input)
AuthService.authenticate()
  ↓ (delegates)
modules.auth.login()
  ↓ (queries)
database.db.get_connection()
  ↓ (queries)
SQLite users table
```

### Cashier Sale Flow
```
CashierView (Product Search)
  ↓ (barcode/keyword)
SalesService.add_to_cart()
  ↓ (validates stock)
ProductService.get_product_by_barcode()
  ↓
modules.products.get_product_by_barcode()
  ↓
database → SQLite

CashierView (Checkout)
  ↓ (payment details)
SalesService.checkout()
  ↓ (processes)
modules.sales.process_sale()
  ↓ (updates inventory)
database → SQLite (INSERT sales, deduct inventory)
```

### Reporting Flow
```
ReportsView (Analytics Tab)
  ↓ (date range)
ReportService.get_sales_range()
  ↓ (queries)
modules.reports.get_sales_by_date_range()
  ↓
database → SQLite (SELECT with aggregation)
```

---

## Permission Model

Controlled at the Service Layer:

```python
Permissions by Role:

ADMIN:
  ✓ View sales
  ✓ Process sales
  ✓ View products
  ✓ Manage products (add/edit/delete)
  ✓ Manage inventory
  ✓ View reports
  ✓ Manage users
  ✓ Manage system

MANAGER:
  ✓ View sales
  ✓ Process sales
  ✓ View products
  ✓ Manage products
  ✓ Manage inventory
  ✓ View reports
  ✗ Manage users
  ✗ Manage system

CASHIER:
  ✓ View sales (today)
  ✓ Process sales
  ✓ View products (read-only)
  ✗ Manage products
  ✗ View reports
  ✗ Manage users
```

---

## Benefits of This Architecture

1. **Separation of Concerns** - Each layer has a single responsibility
2. **Testability** - Services can be tested independently
3. **Maintainability** - Changes to UI don't affect business logic
4. **Reusability** - Services can be used by multiple views
5. **Security** - Permissions enforced at service layer
6. **Scalability** - Easy to add new services/views
7. **Flexibility** - Can swap UI frameworks without changing services

---

## Migration Guide (Gradual Adoption)

The new services layer is **additive and non-breaking**:

### Option 1: Direct View Usage (Existing)
```python
from modules.products import get_all_products
products = get_all_products()  # Works as before
```

### Option 2: Service-Based (New - Recommended)
```python
from services import ProductService
from services.auth_service import AuthService

auth_svc = AuthService()
product_svc = ProductService(auth_svc)
products = product_svc.get_all_products()  # Permission-checked
```

**Both patterns work simultaneously** - no breaking changes!

---

## Next Steps

1. **Update Views Gradually** - Refactor one view at a time to use services
2. **Add Unit Tests** - Test services independently
3. **Add Integration Tests** - Test complete flows
4. **Add DTOs** - Data Transfer Objects for cleaner API contracts
5. **Add Error Handling** - Centralized error handling in service layer
6. **Add Logging** - Audit trail of operations at service layer

---

## File Structure

```
pos_system/
├── main.py                      # Application entry point
├── database/
│   ├── __init__.py
│   └── db.py                    # Database layer (persistence)
├── modules/                     # Business Logic Layer
│   ├── __init__.py
│   ├── auth.py
│   ├── products.py
│   ├── sales.py
│   └── reports.py
├── services/                    # Application Services Layer (NEW)
│   ├── __init__.py
│   ├── auth_service.py
│   ├── product_service.py
│   ├── sales_service.py
│   └── report_service.py
├── views/                       # Presentation Layer (UI)
│   ├── __init__.py
│   ├── login_view.py
│   ├── cashier_view.py
│   ├── product_view.py
│   └── reports_view.py
└── utils/                       # Utilities
    └── __init__.py
```

---

## Example: Building a New Feature

To add a new feature (e.g., Customer Loyalty):

1. **Add business logic** to `modules/customers.py`
   ```python
   def add_loyalty_points(customer_id, points):
       # Pure business rule
   ```

2. **Create service wrapper** in `services/customer_service.py`
   ```python
   class CustomerService:
       def add_points(self, customer_id, points):
           if self.auth_service.user_has_permission('manage_customers'):
               return add_loyalty_points(...)
   ```

3. **Use in view** (e.g., `cashier_view.py`)
   ```python
   customer_svc = CustomerService(auth_svc)
   customer_svc.add_points(customer_id, 50)
   ```

4. **No changes needed** to database layer or authentication!

---

This architecture provides flexibility, maintainability, and scalability while keeping all existing code functional as-is.
