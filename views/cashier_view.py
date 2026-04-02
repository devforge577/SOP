import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from modules.products import search_products, get_product_by_barcode, get_product_by_id, get_low_stock_products
from modules.sales import (
    cart_add_item, cart_remove_item, cart_update_quantity,
    cart_clear, cart_totals, process_sale, get_sale_details,
    get_cart_item_count, get_cart_summary, generate_receipt
)
from modules.reports import get_recent_transactions
import logging
import os
import tempfile
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CashierView(tk.Toplevel):
    """
    Main cashier / POS screen.
    Left panel  → product search & browse
    Centre      → live cart
    Right panel → totals, payment, receipt
    """

    TAX_RATE = 0.0

    def __init__(self, parent, current_user: dict,
                 product_manager=None, sales_processor=None):
        super().__init__(parent)
        self.parent = parent
        self.current_user = current_user
        self.product_manager = product_manager
        self.sales_processor = sales_processor
        self.cart = []
        self.last_sale_id = None
        self.current_customer_id = None
        self.current_customer_name = None

        self.title(f"POS — Cashier ({current_user['full_name']})")
        self.geometry("1280x700")
        self.configure(bg="#f0f2f5")
        self._center_window()
        self._build_ui()
        self._check_low_stock()
        self._update_status_bar()

    def _center_window(self):
        self.update_idletasks()
        w, h = 1280, 700
        x = (self.winfo_screenwidth()  // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ── UI Construction ────────────────────────────────────────────────────

    def _build_ui(self):
        topbar = tk.Frame(self, bg="#1a1a2e", pady=10)
        topbar.pack(fill="x")

        tk.Label(topbar, text="  🛒  Point of Sale",
                 font=("Segoe UI", 14, "bold"),
                 bg="#1a1a2e", fg="white").pack(side="left", padx=10)

        quick_actions = tk.Frame(topbar, bg="#1a1a2e")
        quick_actions.pack(side="left", padx=20)

        tk.Button(quick_actions, text="📱 Scan Barcode",
                  font=("Segoe UI", 9), bg="#0f3460", fg="white",
                  relief="flat", cursor="hand2",
                  command=self._barcode_dialog).pack(side="left", padx=2)

        tk.Button(quick_actions, text="👤 Add Customer",
                  font=("Segoe UI", 9), bg="#0f3460", fg="white",
                  relief="flat", cursor="hand2",
                  command=self._add_customer_dialog).pack(side="left", padx=2)

        info_frame = tk.Frame(topbar, bg="#1a1a2e")
        info_frame.pack(side="right", padx=10)

        tk.Label(info_frame,
                 text=f"Cashier: {self.current_user['full_name']}",
                 font=("Segoe UI", 9), bg="#1a1a2e", fg="#8892b0"
                 ).pack(side="right")

        self.time_var = tk.StringVar()
        self._update_time()
        tk.Label(info_frame, textvariable=self.time_var,
                 font=("Segoe UI", 9), bg="#1a1a2e", fg="#8892b0"
                 ).pack(side="left", padx=10)

        body = tk.Frame(self, bg="#f0f2f5")
        body.pack(fill="both", expand=True, padx=12, pady=10)

        self._build_product_panel(body)
        self._build_cart_panel(body)
        self._build_payment_panel(body)
        self._build_status_bar()

    def _build_status_bar(self):
        self.status_bar = tk.Frame(self, bg="#1a1a2e", height=25)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_label = tk.Label(self.status_bar, text="Ready",
                                      font=("Segoe UI", 8),
                                      bg="#1a1a2e", fg="#8892b0")
        self.status_label.pack(side="left", padx=5, pady=2)
        self.cart_count_label = tk.Label(self.status_bar, text="Items: 0",
                                          font=("Segoe UI", 8),
                                          bg="#1a1a2e", fg="#8892b0")
        self.cart_count_label.pack(side="right", padx=5, pady=2)

    def _update_time(self):
        self.time_var.set(datetime.now().strftime("%H:%M:%S"))
        self.after(1000, self._update_time)

    def _update_status_bar(self):
        item_count = get_cart_item_count(self.cart)
        self.cart_count_label.config(text=f"Items: {item_count}")
        if self.current_customer_name:
            self.status_label.config(text=f"Customer: {self.current_customer_name}")
        else:
            self.status_label.config(text="Ready")

    # ── Left: Product search ───────────────────────────────────────────────

    def _build_product_panel(self, parent):
        frame = tk.Frame(parent, bg="white", bd=0, relief="flat")
        frame.pack(side="left", fill="both", expand=True, padx=(0, 6))

        tk.Label(frame, text="Products", font=("Segoe UI", 11, "bold"),
                 bg="white", fg="#1a1a2e").pack(anchor="w", padx=12, pady=(10, 4))

        search_row = tk.Frame(frame, bg="white")
        search_row.pack(fill="x", padx=12, pady=(0, 6))

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_row, textvariable=self.search_var,
            font=("Segoe UI", 12), relief="flat", bd=3, bg="#f7f8fa")
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=8)
        self.search_entry.bind("<Return>", lambda e: self._search_products())
        self.search_entry.bind("<KeyRelease>", lambda e: self._live_search())
        self.search_entry.focus()

        tk.Button(search_row, text="Search", font=("Segoe UI", 10),
                  bg="#e94560", fg="white", relief="flat", cursor="hand2",
                  command=self._search_products
                  ).pack(side="left", padx=(6, 0), ipady=8, ipadx=6)

        filter_row = tk.Frame(frame, bg="white")
        filter_row.pack(fill="x", padx=12, pady=(0, 6))
        tk.Label(filter_row, text="Category:", bg="white",
                 font=("Segoe UI", 9)).pack(side="left")
        self.category_var = tk.StringVar(value="All")
        self.category_combo = ttk.Combobox(
            filter_row, textvariable=self.category_var,
            values=["All"], state="readonly", width=15)
        self.category_combo.pack(side="left", padx=5)
        self.category_combo.bind("<<ComboboxSelected>>",
                                  lambda e: self._search_products())
        self._load_categories()

        cols = ("Name", "Category", "Price", "Stock")
        self.product_tree = ttk.Treeview(
            frame, columns=cols, show="headings",
            selectmode="browse", height=18)
        col_w = {"Name": 200, "Category": 100, "Price": 80, "Stock": 60}
        for col in cols:
            self.product_tree.heading(col, text=col)
            self.product_tree.column(col, width=col_w[col], anchor="center")
        self.product_tree.column("Name", anchor="w")
        self.product_tree.tag_configure("out_of_stock", foreground="#bbb")
        self.product_tree.tag_configure("low_stock",    foreground="#e94560")

        sb = ttk.Scrollbar(frame, orient="vertical",
                            command=self.product_tree.yview)
        self.product_tree.configure(yscrollcommand=sb.set)
        self.product_tree.pack(side="left", fill="both",
                                expand=True, padx=(12, 0), pady=(0, 10))
        sb.pack(side="left", fill="y", pady=(0, 10))

        self.product_tree.bind("<Double-1>", self._on_product_double_click)
        self.product_tree.bind("<Return>",   self._on_product_double_click)

        self._search_products()

    def _load_categories(self):
        try:
            from modules.products import get_categories
            categories = get_categories()
            self.category_combo['values'] = ["All"] + categories
        except Exception as e:
            logger.error(f"Error loading categories: {e}")

    def _search_products(self):
        keyword  = self.search_var.get().strip()
        category = self.category_var.get()

        if not keyword and category == "All":
            from modules.products import get_all_products
            products = get_all_products()
        elif not keyword:
            from modules.products import get_products_by_category
            products = get_products_by_category(category)
        else:
            products = search_products(keyword)
            if category != "All":
                products = [p for p in products if p.get("category") == category]

        self.product_tree.delete(*self.product_tree.get_children())
        for p in products:
            if p["stock"] == 0:
                tag = "out_of_stock"
            elif p["stock"] <= p.get("low_stock_alert", 5):
                tag = "low_stock"
            else:
                tag = ""
            self.product_tree.insert(
                "", "end", iid=str(p["product_id"]), tags=(tag,),
                values=(
                    p["product_name"],
                    p["category"],
                    f"GHS {p['price']:.2f}",
                    p["stock"]
                ))

    def _live_search(self):
        self._search_products()

    def _on_product_double_click(self, event=None):
        selected = self.product_tree.selection()
        if not selected:
            return
        product = get_product_by_id(int(selected[0]))
        if product:
            self._add_to_cart(product)

    # ── Centre: Cart ───────────────────────────────────────────────────────

    def _build_cart_panel(self, parent):
        frame = tk.Frame(parent, bg="white", bd=0)
        frame.pack(side="left", fill="both", expand=True, padx=6)

        header_row = tk.Frame(frame, bg="white")
        header_row.pack(fill="x", padx=12, pady=(10, 4))

        tk.Label(header_row, text="Cart", font=("Segoe UI", 11, "bold"),
                 bg="white", fg="#1a1a2e").pack(side="left")

        self.customer_label = tk.Label(
            header_row, text="Customer: Walk-in",
            font=("Segoe UI", 9), bg="white", fg="#e94560")
        self.customer_label.pack(side="left", padx=10)

        tk.Button(header_row, text="🗑 Clear Cart",
                  font=("Segoe UI", 9), relief="flat",
                  bg="#e74c3c", fg="white", cursor="hand2",
                  command=self._clear_cart).pack(side="right")

        cart_cols = ("Product", "Qty", "Unit Price", "Subtotal")
        self.cart_tree = ttk.Treeview(
            frame, columns=cart_cols, show="headings",
            selectmode="browse", height=18)
        cart_w = {"Product": 180, "Qty": 50, "Unit Price": 90, "Subtotal": 90}
        for col in cart_cols:
            self.cart_tree.heading(col, text=col)
            self.cart_tree.column(col, width=cart_w[col], anchor="center")
        self.cart_tree.column("Product", anchor="w")

        cart_sb = ttk.Scrollbar(frame, orient="vertical",
                                  command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=cart_sb.set)
        self.cart_tree.pack(side="left", fill="both",
                             expand=True, padx=(12, 0), pady=(0, 10))
        cart_sb.pack(side="left", fill="y", pady=(0, 10))

        self.cart_menu = tk.Menu(self, tearoff=0)
        self.cart_menu.add_command(label="➕  Increase qty", command=self._increase_qty)
        self.cart_menu.add_command(label="➖  Decrease qty", command=self._decrease_qty)
        self.cart_menu.add_separator()
        self.cart_menu.add_command(label="🗑  Remove item",  command=self._remove_from_cart)
        self.cart_tree.bind("<Button-3>", self._show_cart_menu)

    def _show_cart_menu(self, event):
        row = self.cart_tree.identify_row(event.y)
        if row:
            self.cart_tree.selection_set(row)
            self.cart_menu.post(event.x_root, event.y_root)

    # ── Right: Payment ─────────────────────────────────────────────────────

    def _build_payment_panel(self, parent):
        frame = tk.Frame(parent, bg="white", bd=0, width=280)
        frame.pack(side="right", fill="y", padx=(6, 0))
        frame.pack_propagate(False)

        pad = dict(padx=16)

        tk.Label(frame, text="Payment", font=("Segoe UI", 11, "bold"),
                 bg="white", fg="#1a1a2e").pack(anchor="w", pady=(12, 8), **pad)

        totals_frame = tk.Frame(frame, bg="#f7f8fa", pady=10)
        totals_frame.pack(fill="x", padx=12, pady=(0, 10))

        def total_row(label, var, big=False):
            row = tk.Frame(totals_frame, bg="#f7f8fa")
            row.pack(fill="x", padx=10, pady=2)
            font = ("Segoe UI", 13, "bold") if big else ("Segoe UI", 10)
            fg   = "#e94560" if big else "#555"
            tk.Label(row, text=label, font=font, bg="#f7f8fa", fg=fg).pack(side="left")
            tk.Label(row, textvariable=var, font=font, bg="#f7f8fa", fg=fg).pack(side="right")

        self.subtotal_var = tk.StringVar(value="GHS 0.00")
        self.discount_var = tk.StringVar(value="GHS 0.00")
        self.tax_var      = tk.StringVar(value="GHS 0.00")
        self.total_var    = tk.StringVar(value="GHS 0.00")

        total_row("Subtotal", self.subtotal_var)
        total_row("Discount", self.discount_var)
        total_row("Tax",      self.tax_var)
        ttk.Separator(totals_frame).pack(fill="x", padx=10, pady=4)
        total_row("TOTAL",    self.total_var, big=True)

        tk.Label(frame, text="Discount (GHS)", font=("Segoe UI", 9, "bold"),
                 bg="white", fg="#333").pack(anchor="w", **pad)
        self.discount_entry_var = tk.StringVar(value="0")
        tk.Entry(frame, textvariable=self.discount_entry_var,
                 font=("Segoe UI", 11), relief="flat", bd=3,
                 bg="#f7f8fa").pack(fill="x", ipady=6, pady=(2, 10), **pad)
        self.discount_entry_var.trace("w", lambda *a: self._refresh_totals())

        tk.Label(frame, text="Payment Method", font=("Segoe UI", 9, "bold"),
                 bg="white", fg="#333").pack(anchor="w", **pad)
        self.payment_var = tk.StringVar(value="cash")
        for text, val in [("💵 Cash", "cash"),
                           ("📱 Mobile Money", "momo"),
                           ("💳 Card", "card")]:
            tk.Radiobutton(frame, text=text, variable=self.payment_var,
                           value=val, font=("Segoe UI", 10),
                           bg="white", cursor="hand2",
                           activebackground="white").pack(anchor="w", padx=20, pady=2)

        # Mobile Money specific fields (hidden by default)
        self.momo_frame = tk.Frame(frame, bg="white")
        tk.Label(self.momo_frame, text="Phone Number", font=("Segoe UI", 9, "bold"),
                 bg="white", fg="#333").pack(anchor="w", pady=(8, 2))
        self.momo_phone_var = tk.StringVar()
        tk.Entry(self.momo_frame, textvariable=self.momo_phone_var,
                 font=("Segoe UI", 11), relief="flat", bd=3,
                 bg="#f7f8fa").pack(fill="x", ipady=6, pady=(0, 8))

        tk.Label(self.momo_frame, text="Transaction Reference", font=("Segoe UI", 9, "bold"),
                 bg="white", fg="#333").pack(anchor="w", pady=(8, 2))
        self.momo_ref_var = tk.StringVar()
        tk.Entry(self.momo_frame, textvariable=self.momo_ref_var,
                 font=("Segoe UI", 11), relief="flat", bd=3,
                 bg="#f7f8fa").pack(fill="x", ipady=6, pady=(0, 8))

        # Bind payment method change to show/hide MoMo fields
        self.payment_var.trace("w", self._on_payment_method_change)

        tk.Label(frame, text="Amount Paid (GHS)", font=("Segoe UI", 9, "bold"),
                 bg="white", fg="#333").pack(anchor="w", pady=(10, 0), **pad)
        self.amount_paid_var = tk.StringVar(value="0")
        self.amount_entry = tk.Entry(
            frame, textvariable=self.amount_paid_var,
            font=("Segoe UI", 13, "bold"), relief="flat", bd=3, bg="#f7f8fa")
        self.amount_entry.pack(fill="x", ipady=8, pady=(2, 4), **pad)
        self.amount_entry.bind("<KeyRelease>", lambda e: self._refresh_totals())

        self.change_var = tk.StringVar(value="Change: GHS 0.00")
        tk.Label(frame, textvariable=self.change_var,
                 font=("Segoe UI", 10, "bold"), bg="white",
                 fg="#27ae60").pack(anchor="w", **pad)

        tk.Button(frame, text="✔  CHARGE",
                  font=("Segoe UI", 13, "bold"), relief="flat",
                  bg="#e94560", fg="white", cursor="hand2",
                  pady=12, command=self._charge
                  ).pack(fill="x", padx=12, pady=(16, 6))

        # Receipt buttons
        receipt_frame = tk.Frame(frame, bg="white")
        receipt_frame.pack(fill="x", padx=12, pady=4)

        self.receipt_btn = tk.Button(
            receipt_frame, text="🖨  View Receipt",
            font=("Segoe UI", 10), relief="flat",
            bg="#0f3460", fg="white", cursor="hand2",
            pady=8, state="disabled", command=self._show_receipt)
        self.receipt_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.save_receipt_btn = tk.Button(
            receipt_frame, text="💾 Save",
            font=("Segoe UI", 10), relief="flat",
            bg="#1b4332", fg="white", cursor="hand2",
            pady=8, state="disabled", command=self._save_receipt_to_file)
        self.save_receipt_btn.pack(side="left")

        # Quick amounts
        quick_amounts = tk.Frame(frame, bg="white")
        quick_amounts.pack(fill="x", padx=12, pady=5)
        for amount in [20, 50, 100, 200]:
            tk.Button(quick_amounts, text=f"GHS {amount}",
                      font=("Segoe UI", 8), relief="flat",
                      bg="#f0f2f5", fg="#333",
                      command=lambda a=amount: self._set_amount_paid(a)
                      ).pack(side="left", padx=2, expand=True, fill="x")

        self.pay_msg_var = tk.StringVar()
        tk.Label(frame, textvariable=self.pay_msg_var,
                 font=("Segoe UI", 9), bg="white",
                 fg="#e74c3c", wraplength=240).pack(pady=(8, 0), **pad)

    def _on_payment_method_change(self, *args):
        """Show/hide mobile money fields based on payment method."""
        if self.payment_var.get() == "momo":
            self.momo_frame.pack(fill="x", padx=12, pady=(0, 10), after=self.discount_entry_var)
        else:
            self.momo_frame.pack_forget()
            # Clear MoMo fields when not selected
            self.momo_phone_var.set("")
            self.momo_ref_var.set("")

    def _set_amount_paid(self, amount):
        self.amount_paid_var.set(str(amount))

    # ── Cart logic ─────────────────────────────────────────────────────────

    def _add_to_cart(self, product: dict, qty: int = 1):
        if product["stock"] == 0:
            self._pay_msg("Out of stock.", error=True); return
        self.cart, ok, msg = cart_add_item(self.cart, product, qty)
        if not ok:
            self._pay_msg(msg, error=True)
        else:
            self._refresh_cart_tree()
            self._refresh_totals()
            self._update_status_bar()

    def _remove_from_cart(self):
        selected = self.cart_tree.selection()
        if not selected:
            return
        self.cart = cart_remove_item(self.cart, int(selected[0]))
        self._refresh_cart_tree()
        self._refresh_totals()
        self._update_status_bar()

    def _increase_qty(self):
        self._change_qty(+1)

    def _decrease_qty(self):
        self._change_qty(-1)

    def _change_qty(self, delta: int):
        selected = self.cart_tree.selection()
        if not selected:
            return
        product_id = int(selected[0])
        for item in self.cart:
            if item["product_id"] == product_id:
                new_qty = item["quantity"] + delta
                self.cart, ok, msg = cart_update_quantity(
                    self.cart, product_id, new_qty)
                if not ok:
                    self._pay_msg(msg, error=True)
                self._refresh_cart_tree()
                self._refresh_totals()
                self._update_status_bar()
                return

    def _clear_cart(self):
        if not self.cart:
            return
        if messagebox.askyesno("Clear Cart", "Remove all items from the cart?"):
            self.cart = cart_clear(self.cart)
            self._refresh_cart_tree()
            self._refresh_totals()
            self.last_sale_id = None
            self.receipt_btn.config(state="disabled")
            self.save_receipt_btn.config(state="disabled")
            self._pay_msg("")
            self._update_status_bar()

    def _refresh_cart_tree(self):
        self.cart_tree.delete(*self.cart_tree.get_children())
        for item in self.cart:
            self.cart_tree.insert(
                "", "end", iid=str(item["product_id"]),
                values=(
                    item["product_name"],
                    item["quantity"],
                    f"GHS {item['unit_price']:.2f}",
                    f"GHS {item['subtotal']:.2f}",
                ))

    def _refresh_totals(self):
        try:
            discount = float(self.discount_entry_var.get())
        except ValueError:
            discount = 0.0

        totals = cart_totals(self.cart, discount, self.TAX_RATE)
        self.subtotal_var.set(f"GHS {totals['subtotal']:.2f}")
        self.discount_var.set(f"GHS {totals['discount']:.2f}")
        self.tax_var.set(     f"GHS {totals['tax']:.2f}")
        self.total_var.set(   f"GHS {totals['total']:.2f}")

        try:
            paid   = float(self.amount_paid_var.get())
            change = paid - totals["total"]
            self.change_var.set(
                f"Change: GHS {change:.2f}" if change >= 0
                else f"Short: GHS {abs(change):.2f}"
            )
        except ValueError:
            self.change_var.set("Change: GHS 0.00")

    # ── Payment ────────────────────────────────────────────────────────────

    def _charge(self):
        if not self.cart:
            self._pay_msg("Cart is empty.", error=True); return

        try:
            amount_paid = float(self.amount_paid_var.get())
        except ValueError:
            self._pay_msg("Enter a valid amount paid.", error=True); return

        try:
            discount = float(self.discount_entry_var.get())
        except ValueError:
            discount = 0.0

        totals = cart_totals(self.cart, discount, self.TAX_RATE)
        if amount_paid < totals["total"]:
            self._pay_msg(
                f"Insufficient payment. Total: GHS {totals['total']:.2f}",
                error=True)
            return

        # Handle different payment methods
        payment_method = self.payment_var.get()
        if payment_method == "momo":
            # Validate MoMo fields
            phone = self.momo_phone_var.get().strip()
            ref = self.momo_ref_var.get().strip()
            if not phone:
                self._pay_msg("Enter customer phone number for MoMo payment.", error=True)
                return
            if not ref:
                self._pay_msg("Enter transaction reference for MoMo payment.", error=True)
                return

            # Process sale first to get sale_id
            ok, sale_id, change, msg = process_sale(
                cart=self.cart,
                user_id=self.current_user["user_id"],
                payment_method=payment_method,
                amount_paid=amount_paid,
                discount=discount,
                tax_rate=self.TAX_RATE,
                customer_id=self.current_customer_id
            )

            if not ok:
                self._pay_msg(msg, error=True)
                return

            # Process MoMo payment
            from services.payment_service import process_momo_checkout
            success, txn_id, msg = process_momo_checkout(
                user_id=self.current_user["user_id"],
                amount_paid=amount_paid,
                total_amount=totals["total"],
                sale_id=sale_id,
                phone_number=phone,
                reference=ref
            )

            if not success:
                self._pay_msg(f"MoMo payment failed: {msg}", error=True)
                return

            change = amount_paid - totals["total"]  # MoMo doesn't give change
            msg = f"✔ MoMo payment confirmed! Transaction: {txn_id}"

        else:
            # Cash or card payment
            ok, sale_id, change, msg = process_sale(
                cart=self.cart,
                user_id=self.current_user["user_id"],
                payment_method=payment_method,
                amount_paid=amount_paid,
                discount=discount,
                tax_rate=self.TAX_RATE,
                customer_id=self.current_customer_id
            )

            if not ok:
                self._pay_msg(msg, error=True)
                return

        # Handle success for both payment methods
        self.last_sale_id = sale_id
        self._pay_msg(msg, error=False)
        self.receipt_btn.config(state="normal")
        self.save_receipt_btn.config(state="normal")

        self.cart = cart_clear(self.cart)
        self._refresh_cart_tree()
        self._refresh_totals()
        self.discount_entry_var.set("0")
        self.amount_paid_var.set("0")
        self.payment_var.set("cash")

        # Clear MoMo fields
        self.momo_phone_var.set("")
        self.momo_ref_var.set("")

        self.current_customer_id   = None
        self.current_customer_name = None
        self.customer_label.config(text="Customer: Walk-in")

        self._search_products()
        self._check_low_stock()
        self._update_status_bar()

        if messagebox.askyesno("Receipt", "Print receipt?"):
            self._show_receipt()
        else:
            self._pay_msg(msg, error=True)

    # ── Receipt ────────────────────────────────────────────────────────────

    def _show_receipt(self):
        if not self.last_sale_id:
            return
        receipt_text = generate_receipt(self.last_sale_id, "POS System")
        if not receipt_text:
            return

        win = tk.Toplevel(self)
        win.title(f"Receipt — Sale #{self.last_sale_id}")
        win.geometry("420x640")
        win.configure(bg="white")
        win.resizable(False, True)

        text_frame = tk.Frame(win, bg="white")
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)

        text = tk.Text(text_frame, font=("Courier New", 9),
                       bg="white", relief="flat", wrap="word")
        text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(text_frame, orient="vertical",
                                   command=text.yview)
        scrollbar.pack(side="right", fill="y")
        text.configure(yscrollcommand=scrollbar.set)
        text.insert("1.0", receipt_text)
        text.config(state="disabled")

        btn_frame = tk.Frame(win, bg="white")
        btn_frame.pack(fill="x", pady=8, padx=10)

        tk.Button(btn_frame, text="🖨  Print",
                  relief="flat", bg="#0f3460", fg="white",
                  font=("Segoe UI", 10), width=10,
                  command=lambda: self._print_receipt(receipt_text)
                  ).pack(side="left", padx=(0, 6))

        tk.Button(btn_frame, text="💾  Save to File",
                  relief="flat", bg="#1b4332", fg="white",
                  font=("Segoe UI", 10), width=12,
                  command=lambda: self._save_receipt_dialog(receipt_text)
                  ).pack(side="left", padx=(0, 6))

        tk.Button(btn_frame, text="📋  Copy",
                  relief="flat", bg="#444", fg="white",
                  font=("Segoe UI", 10), width=8,
                  command=lambda: self._copy_receipt(receipt_text)
                  ).pack(side="left", padx=(0, 6))

        tk.Button(btn_frame, text="Close",
                  relief="flat", bg="#e94560", fg="white",
                  font=("Segoe UI", 10), width=8,
                  command=win.destroy).pack(side="right")

    def _print_receipt(self, receipt_text: str):
        """
        Print receipt using the OS default text printer.
        On Windows: writes a temp file and sends it to notepad /p.
        On Linux/Mac: uses lpr.
        """
        try:
            import sys
            tmp = tempfile.NamedTemporaryFile(
                mode='w', suffix='.txt',
                delete=False, encoding='utf-8')
            tmp.write(receipt_text)
            tmp.close()

            if sys.platform.startswith("win"):
                os.startfile(tmp.name, "print")
            elif sys.platform == "darwin":
                os.system(f'lpr "{tmp.name}"')
            else:
                os.system(f'lpr "{tmp.name}"')

            self._pay_msg("Sent to printer.", error=False)
            logger.info(f"Receipt for sale #{self.last_sale_id} sent to printer.")
        except Exception as e:
            messagebox.showerror("Print Error",
                                  f"Could not print receipt:\n{str(e)}\n\n"
                                  "Try 'Save to File' instead.")
            logger.error(f"Print error: {e}")

    def _save_receipt_dialog(self, receipt_text: str):
        """Open a Save As dialog and write the receipt to a .txt file."""
        default_name = f"receipt_{self.last_sale_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=default_name,
            title="Save Receipt"
        )
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(receipt_text)
                self._pay_msg(f"Receipt saved.", error=False)
                logger.info(f"Receipt saved to {filepath}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Could not save receipt:\n{str(e)}")

    def _save_receipt_to_file(self):
        """Quick-save from the receipt button without opening receipt window."""
        if not self.last_sale_id:
            return
        receipt_text = generate_receipt(self.last_sale_id, "POS System")
        if receipt_text:
            self._save_receipt_dialog(receipt_text)

    def _copy_receipt(self, receipt_text: str):
        self.clipboard_clear()
        self.clipboard_append(receipt_text)
        self._pay_msg("Receipt copied to clipboard!", error=False)

    # ── Customer Management ────────────────────────────────────────────────

    def _add_customer_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Customer Management")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(dialog, text="Customer Phone:").pack(pady=5)
        phone_entry = tk.Entry(dialog, width=30)
        phone_entry.pack(pady=5)
        phone_entry.focus()

        def search_customer():
            phone = phone_entry.get().strip()
            if not phone:
                return
            try:
                from modules.customers import get_customer_by_phone
                customer = get_customer_by_phone(phone)
                if customer:
                    self.current_customer_id   = customer['customer_id']
                    self.current_customer_name = customer['full_name']
                    pts = customer.get('loyalty_points', 0)
                    self.customer_label.config(
                        text=f"Customer: {customer['full_name']} ({pts} pts)")
                    self._pay_msg(
                        f"Customer: {customer['full_name']} | {pts} loyalty pts",
                        error=False)
                    dialog.destroy()
                else:
                    if messagebox.askyesno("New Customer",
                                           "Customer not found. Create new?"):
                        self._create_customer_dialog(phone)
                        dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error finding customer: {e}")

        phone_entry.bind("<Return>", lambda e: search_customer())
        tk.Button(dialog, text="Search", command=search_customer).pack(pady=10)
        tk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=5)

    def _create_customer_dialog(self, phone=""):
        dialog = tk.Toplevel(self)
        dialog.title("New Customer")
        dialog.geometry("350x300")
        dialog.transient(self)
        dialog.grab_set()

        fields = [("Full Name:", "name"), ("Phone:", "phone"),
                  ("Email:", "email"), ("Address:", "address")]
        entries = {}
        for i, (label, attr) in enumerate(fields):
            tk.Label(dialog, text=label).grid(
                row=i, column=0, sticky="w", padx=5, pady=5)
            entry = tk.Entry(dialog, width=30)
            entry.grid(row=i, column=1, padx=5, pady=5)
            if attr == "phone" and phone:
                entry.insert(0, phone)
            entries[attr] = entry

        def save_customer():
            try:
                from modules.customers import add_customer
                success, msg = add_customer(
                    full_name=entries['name'].get(),
                    phone=entries['phone'].get(),
                    email=entries['email'].get(),
                    address=entries['address'].get()
                )
                if success:
                    messagebox.showinfo("Success", msg)
                    dialog.destroy()
                    self._add_customer_dialog()
                else:
                    messagebox.showerror("Error", msg)
            except Exception as e:
                messagebox.showerror("Error", f"Error creating customer: {e}")

        tk.Button(dialog, text="Save", command=save_customer
                  ).grid(row=4, column=0, columnspan=2, pady=10)

    # ── Barcode Scanner ────────────────────────────────────────────────────

    def _barcode_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Scan Barcode")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(dialog, text="Scan or enter barcode:").pack(pady=10)
        barcode_var = tk.StringVar()
        entry = tk.Entry(dialog, textvariable=barcode_var, font=("Courier", 14))
        entry.pack(pady=5, padx=20, fill="x")
        entry.focus()

        def process_barcode():
            barcode = barcode_var.get().strip()
            if barcode:
                product = get_product_by_barcode(barcode)
                if product:
                    self._add_to_cart(product)
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "Product not found!")
                    barcode_var.set("")
                    entry.focus()

        entry.bind("<Return>", lambda e: process_barcode())
        tk.Button(dialog, text="Add to Cart", command=process_barcode).pack(pady=10)

    # ── Stock Alerts ───────────────────────────────────────────────────────

    def _check_low_stock(self):
        try:
            low_stock = get_low_stock_products()
            if low_stock:
                msg = "⚠️ Low Stock Alert ⚠️\n\n"
                for product in low_stock[:5]:
                    msg += f"• {product['product_name']}: {product['quantity']} units left\n"
                if len(low_stock) > 5:
                    msg += f"\n... and {len(low_stock) - 5} more products"
                messagebox.showwarning("Low Stock Alert", msg)
        except Exception as e:
            logger.error(f"Error checking low stock: {e}")

    # ── Helpers ────────────────────────────────────────────────────────────

    def _pay_msg(self, msg: str, error: bool = False):
        self.pay_msg_var.set(msg)
        color = "#e74c3c" if error else "#27ae60"
        for widget in self.winfo_children():
            self._set_pay_label_color(widget, color)

    def _set_pay_label_color(self, widget, color):
        if (isinstance(widget, tk.Label) and
                str(widget.cget("textvariable")) == str(self.pay_msg_var)):
            widget.config(fg=color)
            return
        for child in widget.winfo_children():
            self._set_pay_label_color(child, color)