# Presentation Layer Documentation

The Presentation Layer contains all user-facing interfaces built with Tkinter. Each view is organized around specific business domains.

## Presentation Layer Components

### 1. Login Screen (`views/login_view.py`)

**Purpose:** User authentication and session initialization  
**User Roles:** All users  
**Architecture Mapping:**
- Presentation: LoginView (Tkinter window with form)
- Service: AuthService (authentication coordination)
- Business Logic: modules.auth.login()
- Data: SQLite users table

**Key Operations:**
```python
# User inputs credentials
username = "cashier"
password = "cashier123"

# Service validates against database
auth_service = AuthService()
success, user, message = auth_service.authenticate(username, password)

# On success, session is created
if success:
    main_dashboard = Dashboard(user)
```

**Permissions Checked:** None (pre-authentication)

---

### 2. Cashier Screen / POS (`views/cashier_view.py`)

**Purpose:** Point of sale interface for processing customer transactions  
**User Roles:** Cashier, Manager, Admin  
**Architecture Mapping:**
- Presentation: CashierView (Product search, cart display, payment)
- Services: 
  - AuthService (verify cashier role)
  - ProductService (search, barcode lookup)
  - SalesService (cart operations, checkout)
- Business Logic: modules.sales, modules.products
- Data: SQLite products, inventory, sales tables

**Key Operations:**

```python
# 1. Authenticate and initialize services
auth_svc = AuthService()
product_svc = ProductService(auth_svc)
sales_svc = SalesService(auth_svc, product_svc)

# 2. User searches products
products = product_svc.search_products("laptop")
# OR scans barcode
product = product_svc.get_product_by_barcode("BAR001")

# 3. Add items to cart
cart = []
cart, ok, msg = sales_svc.add_to_cart(cart, product, qty=2)

# 4. View cart summary
summary = sales_svc.get_cart_summary(cart)
print(f"Cart: {summary['item_count']} items, Total: {summary['total_value']}")

# 5. Process checkout
success, sale_id, change, msg = sales_svc.checkout(
    cart=cart,
    payment_method="cash",
    amount_paid=500.00,
    discount=0,
    tax_rate=0.0
)

# 6. Print receipt
if success:
    receipt = sales_svc.get_receipt(sale_id)
    print(receipt)
```

**Permissions Checked:**
- ✓ process_sale
- ✓ view_products

**Screen Sections:**
- **Left Panel:** Product search & filtering
- **Center Panel:** Shopping cart with live totals
- **Right Panel:** Payment interface (cash/momo/card)
- **Bottom:** Receipt printer & status

---

### 3. Product Management (`views/product_view.py`)

**Purpose:** Admin/Manager interface for product and inventory management  
**User Roles:** Manager, Admin  
**Architecture Mapping:**
- Presentation: ProductView (Product table, CRUD forms)
- Service: ProductService (product operations)
- Business Logic: modules.products
- Data: SQLite products, inventory tables

**Key Operations:**

```python
# Initialize service
auth_svc = AuthService()
product_svc = ProductService(auth_svc)

# 1. List all products
all_products = product_svc.get_all_products(include_inactive=False)

# 2. Search products
results = product_svc.search_products("office chair")

# 3. Get categories for filtering
categories = product_svc.get_categories()

# 4. Add new product (permission-checked)
success, msg = product_svc.add_product(
    product_name="Wireless Mouse",
    category="Electronics",
    price=29.99,
    barcode="BAR123",
    supplier="TechCorp",
    initial_stock=50,
    low_stock_alert=5
)

# 5. Update product
success, msg = product_svc.update_product(
    product_id=42,
    price=24.99,
    low_stock_alert=10
)

# 6. Delete product
success, msg = product_svc.delete_product(product_id=42)

# 7. Check low stock alerts
low_stock = product_svc.get_low_stock_products()
```

**Permissions Checked:**
- ✓ manage_products
- ✓ view_products

**Screen Sections:**
- **Top Tabs:** All Products, Low Stock, Categories
- **Left Panel:** Product table with search & filtering
- **Right Panel:** Product details form
- **Buttons:** Add, Edit, Delete, Restore, Bulk Import

---

### 4. Reports & Analytics (`views/reports_view.py`)

**Purpose:** Business intelligence and performance reporting  
**User Roles:** Manager, Admin  
**Architecture Mapping:**
- Presentation: ReportsView (Multiple tabs for different reports)
- Service: ReportService (analytics coordination)
- Business Logic: modules.reports
- Data: SQLite sales, products, inventory tables

**Key Operations:**

```python
# Initialize service
auth_svc = AuthService()
report_svc = ReportService(auth_svc)

# 1. Daily summary
today = report_svc.get_daily_summary()
print(f"Today's Revenue: {today['total_revenue']}")

# 2. Sales trends
sales_range = report_svc.get_sales_range("2024-01-01", "2024-01-31")
for day in sales_range:
    print(f"{day['sale_date']}: {day['total_revenue']}")

# 3. Top performing products
top_10 = report_svc.get_top_products(limit=10, start_date="2024-01-01", end_date="2024-01-31")
for rank, product in enumerate(top_10, 1):
    print(f"{rank}. {product['product_name']}: {product['units_sold']} units")

# 4. Payment method breakdown
by_method = report_svc.get_payment_breakdown("2024-01-01", "2024-01-31")
for method in by_method:
    print(f"{method['payment_method']}: {method['percentage']}%")

# 5. Cashier performance
performance = report_svc.get_cashier_performance("2024-01-01", "2024-01-31")
for cashier in performance:
    print(f"{cashier['cashier_name']}: {cashier['transactions']} sales")

# 6. Inventory status
inventory = report_svc.get_inventory_status()

# 7. Low stock alerts
low_stock = report_svc.get_low_stock_alert()
```

**Permissions Checked:**
- ✓ view_reports

**Screen Tabs:**
- **Overview:** KPI cards, daily totals, payment breakdown
- **Top Products:** Best sellers by unit and revenue
- **Inventory:** Current stock levels, low stock flags
- **Transactions:** Recent sales, search by date
- **Cashier Performance:** Individual cashier metrics
- **Profit Analysis:** Margin analysis, cost vs revenue
- **Customer Insights:** Loyalty metrics, customer segments

---

## Presentation Layer Data Contracts

### Product Data Structure
```python
{
    'product_id': int,
    'product_name': str,
    'category': str,
    'price': float,
    'barcode': str | None,
    'supplier': str | None,
    'stock': int,
    'low_stock_alert': int,
    'is_active': int (1 or 0),
}
```

### Cart Item Structure
```python
{
    'product_id': int,
    'product_name': str,
    'unit_price': float,
    'quantity': int,
    'subtotal': float,  # quantity * unit_price
}
```

### User/Session Structure
```python
{
    'user_id': int,
    'username': str,
    'full_name': str,
    'role': str,  # 'admin', 'manager', 'cashier'
    'is_active': int (1 or 0),
}
```

### Sale Transaction Structure
```python
{
    'sale_id': int,
    'sale_date': str,
    'total_amount': float,
    'discount': float,
    'tax': float,
    'payment_method': str,  # 'cash', 'momo', 'card'
    'cashier': str,
    'items': [  # List of cart items
        {
            'product_name': str,
            'quantity': int,
            'unit_price': float,
            'subtotal': float,
        }
    ]
}
```

---

## Best Practices for View Implementation

### 1. Initialize Services at View Creation
```python
class CashierView(tk.Toplevel):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        
        # Initialize services with current user context
        auth_svc = AuthService()
        auth_svc.current_session = current_user
        
        self.product_svc = ProductService(auth_svc)
        self.sales_svc = SalesService(auth_svc, self.product_svc)
```

### 2. Check Permissions Before Operations
```python
def on_add_product_clicked(self):
    if not self.product_svc.auth_service.user_has_permission('manage_products'):
        messagebox.showerror("Permission Denied", "You don't have permission to add products")
        return
    
    # Proceed with add product dialog
```

### 3. Handle Service Errors Gracefully
```python
success, msg = self.product_svc.add_product(name, category, price)
if not success:
    messagebox.showerror("Error", msg)
    logger.error(f"Failed to add product: {msg}")
    return

messagebox.showinfo("Success", msg)
```

### 4. Use Service Summaries for Display
```python
def update_cart_display(self):
    summary = self.sales_svc.get_cart_summary(self.cart)
    self.cart_label.config(
        text=f"Items: {summary['item_count']} | Total: ${summary['total_value']:.2f}"
    )
```

### 5. Implement Safe Logout
```python
def on_logout(self):
    success, msg = self.auth_svc.logout()
    self.destroy()
    # Return to login screen
```

---

## Adding New Views

To add a new view (e.g., Customer Management):

1. **Create new file:** `views/customer_view.py`
2. **Create service:** `services/customer_service.py`
3. **Add business logic:** `modules/customers.py`
4. **Update services/__init__.py** to export new service
5. **Update main dashboard** to add navigation button
6. **Initialize service** in Dashboard with auth context
7. **Implement UI** using existing views as templates

No changes needed to database or authentication!
