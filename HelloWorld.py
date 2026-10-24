import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox


class SalonPOS:
    def __init__(self, root):
        self.root = root
        self.root.title("Salon POS & Inventory")
        self.root.geometry("1050x720")
        self.root.minsize(850, 600)
        self.root.configure(bg="#f3f5f9")

        database_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "salon_pos.db")
        self.connection = sqlite3.connect(database_path)
        self.connection.row_factory = sqlite3.Row
        self.cart = []
        self.catalog = {}

        self.create_database()
        self.configure_styles()
        self.create_interface()
        self.refresh_all()
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

    def create_database(self):
        with self.connection:
            self.connection.execute("""CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT '',
                price REAL NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0
            )""")
            self.connection.execute("""CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT '',
                price REAL NOT NULL
            )""")
            self.connection.execute("""CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                total REAL NOT NULL
            )""")
            self.connection.execute("""CREATE TABLE IF NOT EXISTS sale_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                item_type TEXT NOT NULL,
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                line_total REAL NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales(id)
            )""")

            product_count = self.connection.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            service_count = self.connection.execute("SELECT COUNT(*) FROM services").fetchone()[0]
            if product_count == 0:
                self.connection.executemany(
                    "INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)",
                    [("Shampoo", "Hair care", 18.00, 12),
                     ("Conditioner", "Hair care", 20.00, 10),
                     ("Hair mask", "Treatment", 25.00, 6)]
                )
            if service_count == 0:
                self.connection.executemany(
                    "INSERT INTO services (name, category, price) VALUES (?, ?, ?)",
                    [("Haircut", "Styling", 35.00),
                     ("Blow-dry", "Styling", 28.00),
                     ("Color service", "Color", 75.00)]
                )

    def configure_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#f3f5f9")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("TLabel", background="#f3f5f9", foreground="#243047", font=("Arial", 10))
        style.configure("Title.TLabel", font=("Arial", 21, "bold"), foreground="#18243a")
        style.configure("Subtitle.TLabel", foreground="#68758b")
        style.configure("CardTitle.TLabel", background="#ffffff", font=("Arial", 12, "bold"))
        style.configure("TButton", padding=(10, 7), font=("Arial", 10))
        style.configure("Accent.TButton", background="#6655d9", foreground="#ffffff", padding=(12, 9))
        style.map("Accent.TButton", background=[("active", "#5141c2")])
        style.configure("Treeview", rowheight=28, font=("Arial", 10), background="#ffffff", fieldbackground="#ffffff")
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background="#e9edf5")
        style.configure("TNotebook", background="#f3f5f9", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(18, 10), font=("Arial", 10, "bold"))
        style.configure("TLabelframe", background="#ffffff")
        style.configure("TLabelframe.Label", background="#ffffff", font=("Arial", 10, "bold"))

    def create_interface(self):
        header = ttk.Frame(self.root, padding=(24, 20, 24, 12))
        header.pack(fill="x")
        ttk.Label(header, text="Salon POS & Inventory", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="Sales, stock, services, and business snapshots — all stored on this device.",
                  style="Subtitle.TLabel").pack(anchor="w", pady=(4, 0))

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=(4, 20))
        self.pos_tab = ttk.Frame(self.tabs, padding=16)
        self.inventory_tab = ttk.Frame(self.tabs, padding=16)
        self.services_tab = ttk.Frame(self.tabs, padding=16)
        self.reports_tab = ttk.Frame(self.tabs, padding=16)
        self.tabs.add(self.pos_tab, text="  POS  ")
        self.tabs.add(self.inventory_tab, text="  Inventory  ")
        self.tabs.add(self.services_tab, text="  Services  ")
        self.tabs.add(self.reports_tab, text="  Reports  ")

        self.build_pos_tab()
        self.build_inventory_tab()
        self.build_services_tab()
        self.build_reports_tab()

    def make_tree(self, parent, columns, headings, widths):
        tree = ttk.Treeview(parent, columns=columns, show="headings", selectmode="browse")
        for column, heading, width in zip(columns, headings, widths):
            tree.heading(column, text=heading)
            tree.column(column, width=width, anchor="w")
        return tree

    def build_pos_tab(self):
        self.pos_tab.columnconfigure(0, weight=3)
        self.pos_tab.columnconfigure(1, weight=2)
        self.pos_tab.rowconfigure(0, weight=1)

        left = ttk.Frame(self.pos_tab, style="Card.TFrame", padding=16)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        right = ttk.Frame(self.pos_tab, style="Card.TFrame", padding=16)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        ttk.Label(left, text="New sale", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 14))

        picker = ttk.Frame(left, style="Card.TFrame")
        picker.pack(fill="x")
        ttk.Label(picker, text="Item", background="#ffffff").grid(row=0, column=0, sticky="w")
        ttk.Label(picker, text="Qty", background="#ffffff").grid(row=0, column=1, sticky="w", padx=(10, 0))
        self.pos_item = ttk.Combobox(picker, state="readonly", width=35)
        self.pos_item.grid(row=1, column=0, sticky="ew", pady=(4, 10))
        self.pos_quantity = ttk.Entry(picker, width=8)
        self.pos_quantity.insert(0, "1")
        self.pos_quantity.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=(4, 10))
        ttk.Button(picker, text="Add to sale", command=self.add_to_cart).grid(row=1, column=2, padx=(10, 0), pady=(4, 10))
        picker.columnconfigure(0, weight=1)

        self.cart_tree = self.make_tree(left, ("item", "qty", "price", "total"),
                                        ("Item", "Qty", "Price", "Total"), (220, 55, 80, 90))
        self.cart_tree.pack(fill="both", expand=True, pady=(8, 12))
        cart_actions = ttk.Frame(left, style="Card.TFrame")
        cart_actions.pack(fill="x")
        ttk.Button(cart_actions, text="Remove selected", command=self.remove_cart_item).pack(side="left")
        ttk.Button(cart_actions, text="Clear", command=self.clear_cart).pack(side="left", padx=8)

        ttk.Label(right, text="Sale summary", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 16))
        ttk.Label(right, text="Amount due", background="#ffffff", foreground="#68758b").pack(anchor="w")
        self.total_label = ttk.Label(right, text="$0.00", background="#ffffff",
                                     foreground="#5141c2", font=("Arial", 28, "bold"))
        self.total_label.pack(anchor="w", pady=(2, 18))
        ttk.Button(right, text="Complete sale", style="Accent.TButton",
                   command=self.complete_sale).pack(fill="x")
        ttk.Label(right, text="Product quantities are deducted from inventory when a sale is completed.",
                  background="#ffffff", foreground="#68758b", wraplength=230,
                  justify="left").pack(anchor="w", pady=(16, 0))

    def build_inventory_tab(self):
        self.inventory_tab.columnconfigure(0, weight=1)
        self.inventory_tab.rowconfigure(0, weight=1)
        card = ttk.Frame(self.inventory_tab, style="Card.TFrame", padding=16)
        card.grid(row=0, column=0, sticky="nsew")
        card.columnconfigure(0, weight=1)
        card.rowconfigure(0, weight=1)
        self.product_tree = self.make_tree(card, ("id", "name", "category", "price", "stock"),
                                           ("ID", "Product", "Category", "Price", "In stock"),
                                           (55, 250, 170, 100, 100))
        self.product_tree.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(0, 14))
        self.product_tree.bind("<<TreeviewSelect>>", self.select_product)

        form = ttk.Frame(card, style="Card.TFrame")
        form.grid(row=1, column=0, sticky="ew")
        self.product_name = self.add_form_field(form, "Product name", 0)
        self.product_category = self.add_form_field(form, "Category", 1)
        self.product_price = self.add_form_field(form, "Price", 2)
        self.product_stock = self.add_form_field(form, "Stock quantity", 3)
        buttons = ttk.Frame(card, style="Card.TFrame")
        buttons.grid(row=1, column=1, sticky="e", padx=(18, 0))
        ttk.Button(buttons, text="Add product", command=self.add_product).pack(fill="x", pady=3)
        ttk.Button(buttons, text="Update selected", command=self.update_product).pack(fill="x", pady=3)
        ttk.Button(buttons, text="Delete selected", command=self.delete_product).pack(fill="x", pady=3)
        ttk.Button(buttons, text="Clear form", command=self.clear_product_form).pack(fill="x", pady=3)

    def build_services_tab(self):
        self.services_tab.columnconfigure(0, weight=1)
        self.services_tab.rowconfigure(0, weight=1)
        card = ttk.Frame(self.services_tab, style="Card.TFrame", padding=16)
        card.grid(row=0, column=0, sticky="nsew")
        card.columnconfigure(0, weight=1)
        card.rowconfigure(0, weight=1)
        self.service_tree = self.make_tree(card, ("id", "name", "category", "price"),
                                           ("ID", "Service", "Category", "Price"),
                                           (55, 300, 220, 120))
        self.service_tree.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(0, 14))
        self.service_tree.bind("<<TreeviewSelect>>", self.select_service)

        form = ttk.Frame(card, style="Card.TFrame")
        form.grid(row=1, column=0, sticky="ew")
        self.service_name = self.add_form_field(form, "Service name", 0)
        self.service_category = self.add_form_field(form, "Category", 1)
        self.service_price = self.add_form_field(form, "Price", 2)
        buttons = ttk.Frame(card, style="Card.TFrame")
        buttons.grid(row=1, column=1, sticky="e", padx=(18, 0))
        ttk.Button(buttons, text="Add service", command=self.add_service).pack(fill="x", pady=3)
        ttk.Button(buttons, text="Update selected", command=self.update_service).pack(fill="x", pady=3)
        ttk.Button(buttons, text="Delete selected", command=self.delete_service).pack(fill="x", pady=3)
        ttk.Button(buttons, text="Clear form", command=self.clear_service_form).pack(fill="x", pady=3)

    def build_reports_tab(self):
        self.reports_tab.columnconfigure(0, weight=1)
        self.reports_tab.rowconfigure(1, weight=1)
        summary = ttk.Frame(self.reports_tab, style="Card.TFrame", padding=18)
        summary.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        ttk.Label(summary, text="Total recorded sales", background="#ffffff", foreground="#68758b").pack(anchor="w")
        self.revenue_label = ttk.Label(summary, text="$0.00", background="#ffffff",
                                       foreground="#5141c2", font=("Arial", 25, "bold"))
        self.revenue_label.pack(anchor="w", pady=(4, 0))
        history = ttk.Frame(self.reports_tab, style="Card.TFrame", padding=16)
        history.grid(row=1, column=0, sticky="nsew")
        history.columnconfigure(0, weight=1)
        history.rowconfigure(1, weight=1)
        top = ttk.Frame(history, style="Card.TFrame")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(top, text="Sales history", style="CardTitle.TLabel").pack(side="left")
        ttk.Button(top, text="Refresh", command=self.refresh_reports).pack(side="right")
        self.report_tree = self.make_tree(history, ("id", "date", "items", "total"),
                                          ("Sale #", "Date", "Items", "Total"),
                                          (85, 190, 430, 120))
        self.report_tree.grid(row=1, column=0, sticky="nsew")

    def add_form_field(self, parent, label, column):
        holder = ttk.Frame(parent, style="Card.TFrame")
        holder.grid(row=0, column=column, sticky="ew", padx=(0, 10))
        ttk.Label(holder, text=label, background="#ffffff").pack(anchor="w", pady=(0, 4))
        entry = ttk.Entry(holder, width=19)
        entry.pack(fill="x")
        return entry

    def refresh_all(self):
        self.refresh_products()
        self.refresh_services()
        self.refresh_pos_catalog()
        self.refresh_reports()

    def refresh_products(self):
        for row in self.product_tree.get_children():
            self.product_tree.delete(row)
        rows = self.connection.execute("SELECT * FROM products ORDER BY name").fetchall()
        for row in rows:
            self.product_tree.insert("", "end", values=(row["id"], row["name"], row["category"],
                                                           "${:.2f}".format(row["price"]), row["stock"]))

    def refresh_services(self):
        for row in self.service_tree.get_children():
            self.service_tree.delete(row)
        rows = self.connection.execute("SELECT * FROM services ORDER BY name").fetchall()
        for row in rows:
            self.service_tree.insert("", "end", values=(row["id"], row["name"], row["category"],
                                                           "${:.2f}".format(row["price"])))

    def refresh_pos_catalog(self):
        labels = []
        self.catalog = {}
        for row in self.connection.execute("SELECT * FROM products ORDER BY name").fetchall():
            label = "Product: {} — ${:.2f} (stock: {})".format(row["name"], row["price"], row["stock"])
            labels.append(label)
            self.catalog[label] = {"type": "Product", "id": row["id"], "name": row["name"],
                                   "price": row["price"], "stock": row["stock"]}
        for row in self.connection.execute("SELECT * FROM services ORDER BY name").fetchall():
            label = "Service: {} — ${:.2f}".format(row["name"], row["price"])
            labels.append(label)
            self.catalog[label] = {"type": "Service", "id": row["id"], "name": row["name"],
                                   "price": row["price"]}
        self.pos_item["values"] = labels
        if labels and self.pos_item.get() not in labels:
            self.pos_item.current(0)

    def parse_price(self, value):
        try:
            price = float(value.strip())
        except (ValueError, AttributeError):
            raise ValueError("Enter a valid price, such as 25.00.")
        if price < 0:
            raise ValueError("Price cannot be negative.")
        return price

    def add_product(self):
        name = self.product_name.get().strip()
        if not name:
            messagebox.showerror("Missing product name", "Enter a product name.")
            return
        try:
            price = self.parse_price(self.product_price.get())
            stock = int(self.product_stock.get().strip())
            if stock < 0:
                raise ValueError("Stock cannot be negative.")
        except ValueError as error:
            messagebox.showerror("Check product details", str(error) or "Stock must be a whole number.")
            return
        with self.connection:
            self.connection.execute("INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)",
                                    (name, self.product_category.get().strip(), price, stock))
        self.clear_product_form()
        self.refresh_all()

    def update_product(self):
        selected = self.product_tree.selection()
        if not selected:
            messagebox.showinfo("Select a product", "Choose a product to update.")
            return
        product_id = self.product_tree.item(selected[0], "values")[0]
        name = self.product_name.get().strip()
        if not name:
            messagebox.showerror("Missing product name", "Enter a product name.")
            return
        try:
            price = self.parse_price(self.product_price.get())
            stock = int(self.product_stock.get().strip())
            if stock < 0:
                raise ValueError("Stock cannot be negative.")
        except ValueError as error:
            messagebox.showerror("Check product details", str(error) or "Stock must be a whole number.")
            return
        with self.connection:
            self.connection.execute("UPDATE products SET name=?, category=?, price=?, stock=? WHERE id=?",
                                    (name, self.product_category.get().strip(), price, stock, product_id))
        self.clear_product_form()
        self.refresh_all()

    def delete_product(self):
        selected = self.product_tree.selection()
        if not selected:
            messagebox.showinfo("Select a product", "Choose a product to delete.")
            return
        product_id = self.product_tree.item(selected[0], "values")[0]
        if messagebox.askyesno("Delete product", "Delete this product from inventory?"):
            with self.connection:
                self.connection.execute("DELETE FROM products WHERE id=?", (product_id,))
            self.clear_product_form()
            self.refresh_all()

    def select_product(self, event=None):
        selected = self.product_tree.selection()
        if not selected:
            return
        product_id = self.product_tree.item(selected[0], "values")[0]
        row = self.connection.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
        if row:
            self.set_entries(((self.product_name, row["name"]),
                              (self.product_category, row["category"]),
                              (self.product_price, str(row["price"])),
                              (self.product_stock, str(row["stock"]))))

    def clear_product_form(self):
        self.set_entries(((self.product_name, ""), (self.product_category, ""),
                          (self.product_price, ""), (self.product_stock, "")))
        for item in self.product_tree.selection():
            self.product_tree.selection_remove(item)

    def add_service(self):
        name = self.service_name.get().strip()
        if not name:
            messagebox.showerror("Missing service name", "Enter a service name.")
            return
        try:
            price = self.parse_price(self.service_price.get())
        except ValueError as error:
            messagebox.showerror("Check service details", str(error))
            return
        with self.connection:
            self.connection.execute("INSERT INTO services (name, category, price) VALUES (?, ?, ?)",
                                    (name, self.service_category.get().strip(), price))
        self.clear_service_form()
        self.refresh_all()

    def update_service(self):
        selected = self.service_tree.selection()
        if not selected:
            messagebox.showinfo("Select a service", "Choose a service to update.")
            return
        service_id = self.service_tree.item(selected[0], "values")[0]
        name = self.service_name.get().strip()
        if not name:
            messagebox.showerror("Missing service name", "Enter a service name.")
            return
        try:
            price = self.parse_price(self.service_price.get())
        except ValueError as error:
            messagebox.showerror("Check service details", str(error))
            return
        with self.connection:
            self.connection.execute("UPDATE services SET name=?, category=?, price=? WHERE id=?",
                                    (name, self.service_category.get().strip(), price, service_id))
        self.clear_service_form()
        self.refresh_all()

    def delete_service(self):
        selected = self.service_tree.selection()
        if not selected:
            messagebox.showinfo("Select a service", "Choose a service to delete.")
            return
        service_id = self.service_tree.item(selected[0], "values")[0]
        if messagebox.askyesno("Delete service", "Delete this service from the menu?"):
            with self.connection:
                self.connection.execute("DELETE FROM services WHERE id=?", (service_id,))
            self.clear_service_form()
            self.refresh_all()

    def select_service(self, event=None):
        selected = self.service_tree.selection()
        if not selected:
            return
        service_id = self.service_tree.item(selected[0], "values")[0]
        row = self.connection.execute("SELECT * FROM services WHERE id=?", (service_id,)).fetchone()
        if row:
            self.set_entries(((self.service_name, row["name"]),
                              (self.service_category, row["category"]),
                              (self.service_price, str(row["price"]))))

    def clear_service_form(self):
        self.set_entries(((self.service_name, ""), (self.service_category, ""),
                          (self.service_price, "")))
        for item in self.service_tree.selection():
            self.service_tree.selection_remove(item)

    def set_entries(self, entries):
        for entry, value in entries:
            entry.delete(0, "end")
            entry.insert(0, value)

    def add_to_cart(self):
        label = self.pos_item.get()
        if label not in self.catalog:
            messagebox.showinfo("Choose an item", "Select a product or service first.")
            return
        try:
            quantity = int(self.pos_quantity.get().strip())
            if quantity < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid quantity", "Quantity must be a whole number greater than zero.")
            return
        item = self.catalog[label]
        if item["type"] == "Product" and quantity > item["stock"]:
            messagebox.showerror("Not enough stock", "Only {} unit(s) are currently in stock.".format(item["stock"]))
            return
        self.cart.append({"type": item["type"], "id": item["id"], "name": item["name"],
                          "quantity": quantity, "price": float(item["price"])})
        self.refresh_cart()

    def refresh_cart(self):
        for row in self.cart_tree.get_children():
            self.cart_tree.delete(row)
        total = 0.0
        for index, item in enumerate(self.cart):
            line_total = item["quantity"] * item["price"]
            total += line_total
            self.cart_tree.insert("", "end", iid=str(index),
                                  values=("{}: {}".format(item["type"], item["name"]), item["quantity"],
                                          "${:.2f}".format(item["price"]), "${:.2f}".format(line_total)))
        self.total_label.configure(text="${:.2f}".format(total))

    def remove_cart_item(self):
        selected = self.cart_tree.selection()
        if selected:
            del self.cart[int(selected[0])]
            self.refresh_cart()

    def clear_cart(self):
        self.cart = []
        self.refresh_cart()

    def complete_sale(self):
        if not self.cart:
            messagebox.showinfo("Empty sale", "Add at least one item before completing the sale.")
            return
        total = sum(item["quantity"] * item["price"] for item in self.cart)
        try:
            with self.connection:
                for item in self.cart:
                    if item["type"] == "Product":
                        current = self.connection.execute(
                            "SELECT stock FROM products WHERE id=?", (item["id"],)).fetchone()
                        if current is None or current["stock"] < item["quantity"]:
                            raise ValueError("Not enough stock for {}. Review inventory and try again.".format(item["name"]))
                cursor = self.connection.execute("INSERT INTO sales (total) VALUES (?)", (total,))
                sale_id = cursor.lastrowid
                for item in self.cart:
                    line_total = item["quantity"] * item["price"]
                    self.connection.execute(
                        "INSERT INTO sale_lines (sale_id, item_type, item_name, quantity, unit_price, line_total) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (sale_id, item["type"], item["name"], item["quantity"], item["price"], line_total))
                    if item["type"] == "Product":
                        self.connection.execute("UPDATE products SET stock=stock-? WHERE id=?",
                                                (item["quantity"], item["id"]))
        except ValueError as error:
            messagebox.showerror("Sale not completed", str(error))
            self.refresh_all()
            return
        messagebox.showinfo("Sale complete", "Sale #{} recorded for ${:.2f}.".format(sale_id, total))
        self.clear_cart()
        self.refresh_all()

    def refresh_reports(self):
        if not hasattr(self, "report_tree"):
            return
        for row in self.report_tree.get_children():
            self.report_tree.delete(row)
        sales = self.connection.execute("SELECT * FROM sales ORDER BY id DESC").fetchall()
        revenue = 0.0
        for sale in sales:
            revenue += sale["total"]
            lines = self.connection.execute(
                "SELECT item_name, quantity FROM sale_lines WHERE sale_id=? ORDER BY id", (sale["id"],)).fetchall()
            item_summary = ", ".join("{} x{}".format(line["item_name"], line["quantity"]) for line in lines)
            self.report_tree.insert("", "end", values=(sale["id"], sale["sale_date"], item_summary,
                                                          "${:.2f}".format(sale["total"])))
        self.revenue_label.configure(text="${:.2f}".format(revenue))

    def close_app(self):
        self.connection.close()
        self.root.destroy()


if __name__ == "__main__":
    window = tk.Tk()
    app = SalonPOS(window)
    window.mainloop()
