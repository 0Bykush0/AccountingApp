import os
import sys
import time
import sqlite3
import threading
import tkinter as tk
# from tkinter import ttk
import ttkbootstrap as ttk
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from calendar import monthrange
from ttkbootstrap.widgets import DateEntry
from selenium.webdriver.common.by import By
from tkinter import messagebox, simpledialog
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class AccountingApp:
    def __init__(self, root, theme):
        self.root = root
        self.root.title("Accounting App")
        self.theme = theme  # Store the theme name

        # Initialize database
        print("Initializing database...")
        self.conn = sqlite3.connect('accounting.db')
        self.conn.row_factory = dict_factory  # Set custom row factory
        self.cursor = self.conn.cursor()
        self.create_tables()

        # Initialize variables
        print("Initializing variables...")
        self.transaction_type = tk.StringVar()
        self.transaction_table = ttk.Treeview(root)
        self.shopping_tree = ttk.Treeview(root)
        self.total_expense_label = ttk.Label()
        self.total_income_label = ttk.Label()
        self.net_worth_label = ttk.Label()

        # Create GUI
        print("Creating GUI...")
        self.create_income_expense_widgets()
        self.create_income_expense_table()
        self.create_shopping_page()

        self.style = ttk.Style()
        self.style.configure('Treeview', font=('Arial Rounded MT Bold', 15))
        self.style.configure('TLabel', font=('Arial Rounded MT Bold', 17))
        self.style.configure('TButton', font=('Arial Rounded MT Bold', 16))
        self.style.configure('TCheckbutton', font=('Arial Rounded MT Bold', 17))

        self.title_entry.grid_remove()  # Title entry'yi gizle

        # Set default monthly transactions date
        self.set_default_monthly_transactions_day()

        # Load initial data
        print("loading initial data...")
        self.load_initial_data()
        self.load_shopping_data()
        print("initial data successfully loaded")

    def create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS transactions
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                            date DATE,
                            description TEXT,
                            amount REAL,
                            type TEXT)''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS shopping_list
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                            item TEXT,
                            price REAL)''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS settings
                                (name TEXT PRIMARY KEY,
                                value TEXT)''')

        self.conn.commit()

    def create_income_expense_widgets(self):
        frame = ttk.LabelFrame(self.root, text="Income & Expenses")
        frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        # Make frame fill available horizontal space
        frame.grid_columnconfigure(0, weight=1)

        def update_combobox_items():
            selected_type = self.transaction_type.get()
            if selected_type == "Income":
                items = ["Burs", "Harçlık", "Part-time", "İş-Staj", "Satış", "Freelance", "Reklam", "Others"]
            elif selected_type == "Expense":
                items = ["Yeme-İçme", "Borç", "Yatırım", "Eğlence", "Seyahat", "Market", "Hobil", "Sağlık", "Giyim",
                         "Elektronik", "Spor", "Abonelik", "Others"]
            self.selected_type = selected_type
            self.title_combobox.config(values=items)

        income_checkbox = ttk.Checkbutton(frame, text="Income", variable=self.transaction_type, onvalue="Income",
                                          offvalue="", command=update_combobox_items)
        income_checkbox.grid(row=0, column=0, padx=10, pady=5, sticky='ew')

        expense_checkbox = ttk.Checkbutton(frame, text="Expense", variable=self.transaction_type, onvalue="Expense",
                                           offvalue="", command=update_combobox_items)
        expense_checkbox.grid(row=0, column=1, padx=10, pady=5, sticky='ew')

        self.title_label = ttk.Label(frame, text="Title:")
        self.title_label.grid(row=1, column=0, padx=10, sticky='w')

        self.title_combobox = ttk.Combobox(frame, state="readonly")
        self.title_combobox.grid(row=1, column=1, padx=5, pady=5, sticky='e')
        self.title_combobox.bind("<<ComboboxSelected>>", self.on_combobox_select)

        self.title_entry = ttk.Entry(frame)
        self.title_entry.grid(row=1, column=2, padx=5, pady=5, sticky='e')

        self.amount_label = ttk.Label(frame, text="Amount:")
        self.amount_label.grid(row=2, column=0, padx=10, sticky='w')
        self.amount_entry = ttk.Entry(frame, width=20)
        self.amount_entry.grid(row=2, column=1, padx=5, pady=5, sticky='ew')

        self.date_label = ttk.Label(frame, text="Date:")
        self.date_label.grid(row=3, column=0, padx=10, sticky='w')
        self.date_entry = DateEntry(frame, width=12)
        self.date_entry.grid(row=3, column=1, padx=5, pady=5, sticky='w')

        self.submit_button = ttk.Button(frame, text="Submit", bootstyle='success', command=self.add_transaction)
        self.submit_button.grid(row=4, column=1, columnspan=1, pady=10, padx=10, sticky='ew')

        self.refresh_button = ttk.Button(frame, text="Refresh", bootstyle="info", command=self.load_initial_data)
        self.refresh_button.grid(row=4, column=0, pady=10, padx=10, sticky='ew')

        # Add labels for total income, total expenses, and net worth
        ttk.Label(frame, text="Total Income:").grid(row=5, column=0, padx=10, sticky='w')
        self.total_income_label = ttk.Label(frame, text="")
        self.total_income_label.grid(row=5, column=1, padx=10, sticky='w')

        ttk.Label(frame, text="Total Expenses:").grid(row=6, column=0, padx=10, sticky='w')
        self.total_expense_label = ttk.Label(frame, text="")
        self.total_expense_label.grid(row=6, column=1, padx=10, sticky='w')

        ttk.Label(frame, text="Net Worth:").grid(row=7, column=0, padx=10, sticky='w')
        self.net_worth_label = ttk.Label(frame, text="")
        self.net_worth_label.grid(row=7, column=1, padx=10, sticky='w')

        # Create settings button
        self.settings_button = ttk.Button(frame, text="Settings", command=self.open_settings)
        self.settings_button.grid(row=8, columnspan=2, padx=5, pady=15)

    def create_income_expense_table(self):
        frame = ttk.LabelFrame(self.root, text="Income & Expense Table")
        frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')

        # Make frame expand to fill available space vertically
        self.root.grid_rowconfigure(1, weight=1)

        # Use a hidden column for the ID
        self.transaction_table = ttk.Treeview(frame, columns=("Date", "Title", "Amount", "Type", "ID"), show="headings")
        self.transaction_table.heading("Date", text="Date")
        self.transaction_table.heading("Title", text="Title")
        self.transaction_table.heading("Amount", text="Amount")
        self.transaction_table.heading("Type", text="Type")
        self.transaction_table.heading("ID", text="ID", anchor=tk.CENTER)  # Hide this column heading
        self.transaction_table.column("ID", width=0, stretch=tk.NO)  # Hide this column

        self.transaction_table.grid(row=0, column=0, padx=5, sticky='nsew')

        # Make treeview expand to fill available space
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        # Add remove button
        remove_button = ttk.Button(frame, text="Remove", bootstyle='danger', command=self.remove_transaction)
        remove_button.grid(row=1, column=0, pady=5)

        # Add this line to check if the button is enabled/disabled based on selection
        self.transaction_table.bind("<ButtonRelease-1>", lambda event: remove_button.config(
            state=tk.NORMAL) if self.transaction_table.selection() else remove_button.config(state=tk.DISABLED))

        # Change row colors based on transaction type
        self.transaction_table.tag_configure('expense', background='red')
        self.transaction_table.tag_configure('income', background='green')
        self.transaction_table.tag_configure('shopping', background='purple')

    def create_shopping_page(self):
        frame = ttk.LabelFrame(self.root, text="Shopping List")
        frame.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')

        # Make frame fill available horizontal space
        frame.grid_columnconfigure(0, weight=1)

        # Configure the existing style with new properties
        self.shopping_tree = ttk.Treeview(frame, columns=("Id", "Name", "Price"), show="headings")
        self.shopping_tree.heading("Id", text="Id", anchor=tk.CENTER)
        self.shopping_tree.heading("Name", text="Name", anchor=tk.CENTER)
        self.shopping_tree.heading("Price", text="Price", anchor=tk.CENTER)
        self.shopping_tree.column("Id", width=10, anchor=tk.CENTER)
        self.shopping_tree.column("Name", width=100, anchor=tk.CENTER)
        self.shopping_tree.column("Price", width=100, anchor=tk.CENTER)
        self.shopping_tree.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        self.shopping_tree.grid_configure(ipady=2)

        # Create a frame for buttons
        addItem_frame = ttk.Frame(frame)
        addItem_frame.grid(row=1, column=0, pady=10, sticky='we')

        ttk.Label(addItem_frame, text="Enter item's name:").grid(row=0, column=0, padx=5, pady=5, sticky='ew')
        self.shopping_item = ttk.Entry(addItem_frame, )
        self.shopping_item.grid(row=1, column=0, padx=5, pady=5, sticky='we')
        ttk.Label(addItem_frame, text="Enter item's price:").grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        self.shopping_item_price = ttk.Entry(addItem_frame, )
        self.shopping_item_price.grid(row=1, column=1, padx=5, pady=5, sticky='we')

        addItem_frame.grid_columnconfigure(0, weight=1)
        addItem_frame.grid_columnconfigure(1, weight=1)
        addItem_frame.grid_columnconfigure(2, weight=1)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, padx=5, pady=10, sticky='ew')
        # Add item button for shopping list
        add_item_button = ttk.Button(button_frame, text="Add Item", command=self.add_shopping_item)
        add_item_button.grid(row=0, column=0, padx=5, sticky='ew')

        # Add remove button for shopping list
        remove_shopping_button = ttk.Button(button_frame, text="Remove", bootstyle='danger',
                                            command=self.remove_shopping_item)
        remove_shopping_button.grid(row=0, column=1, padx=5, sticky='ew')

        refresh_button = ttk.Button(button_frame, text="Refresh", bootstyle="info", command=self.load_shopping_data)
        refresh_button.grid(row=0, column=2, pady=5, padx=5, sticky='ew')

        # Add mark as purchased button for shopping list
        mark_purchased_button = ttk.Button(button_frame, text="Mark as Purchased", bootstyle='success',
                                           command=self.mark_as_purchased_shopping)
        mark_purchased_button.grid(row=0, column=3, padx=5, sticky='ew')

        # Center the button frame horizontally
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)

    def add_shopping_item(self):
        item = self.shopping_item.get().capitalize()
        price = self.shopping_item_price.get()

        if not item and price:
            messagebox.showwarning("Warning", "Please fill in all fields.")
            return

        self.cursor.execute("INSERT INTO shopping_list (item, price) VALUES (?, ?)", (item, price))
        self.conn.commit()
        self.load_initial_data()

    def load_shopping_data(self):
        amazon_thread = threading.Thread(target=initialize_amazon_data, args=(self,))
        amazon_thread.start()
        # Fetch shopping list
        self.shopping_tree.delete(*self.shopping_tree.get_children())

        self.cursor.execute("SELECT * FROM shopping_list")
        shopping_list = self.cursor.fetchall()

        for index, shopping_item in enumerate(shopping_list):
            self.shopping_tree.insert("", "end",
                                      values=(index + 1, shopping_item['item'], shopping_item['price'],))

    def on_combobox_select(self, event):
        selected_title = self.title_combobox.get()
        if selected_title in ("Others", "Borç"):
            self.title_entry.delete(0, tk.END)  # Entry'yi temizle
            # self.title_combobox.grid_remove()  # ComboBox'ı gizle
            self.title_entry.grid(row=1, column=2, padx=2, pady=2, sticky='ew')  # Title entry'yi göster
        else:
            self.title_entry.grid_remove()  # Title entry'yi gizle
            self.title_combobox.grid(row=1, column=1, padx=5, pady=5, sticky='w')  # ComboBox'ı göster

    def add_transaction(self):
        transaction_type = self.transaction_type.get()
        title_entry = f"{self.title_entry.get().capitalize()}({self.title_combobox.get()})"
        title = f"{title_entry if self.title_entry.get() != "" else self.title_combobox.get()}"
        amount = self.amount_entry.get()
        date = self.date_entry.entry  # Kullanıcının girdiği tarihi al

        if not (transaction_type and (
                title or (self.title_combobox.get() and self.title_combobox.get() != 'Others')) and amount and date):
            messagebox.showwarning("Warning", "Please fill in all fields.")
            return

        self.cursor.execute("INSERT INTO transactions (date, description, amount, type) VALUES (?, ?, ?, ?)",
                            (datetime.now(), title, amount, transaction_type))
        self.conn.commit()

        # Güncellenmiş verileri yükle
        self.load_initial_data()
        self.clear_fields()

    def load_initial_data(self):
        print("Initializing ")
        self.transaction_table.delete(*self.transaction_table.get_children())

        # Fetch transactions from database
        self.cursor.execute("SELECT * FROM transactions")
        transactions = self.cursor.fetchall()

        total_income = 0
        total_expense = 0

        # Iterate over fetched transactions
        for transaction in transactions:
            formatted_date = transaction['date'].strftime('%Y-%m-%d')
            if transaction['type'] == 'Income':
                self.transaction_table.insert("", "end", values=(
                    formatted_date, transaction['description'], transaction['amount'], transaction['type'],
                    transaction['id']), tags=('income',))
                total_income += transaction['amount']
            elif transaction['type'] == 'Expense':
                self.transaction_table.insert("", "end", values=(
                    formatted_date, transaction['description'], transaction['amount'], transaction['type'],
                    transaction['id']), tags=('expense',))
                total_expense += transaction['amount']
            elif transaction['type'] == 'Shopping':
                self.transaction_table.insert("", "end", values=(
                    formatted_date, transaction['description'], transaction['amount'], transaction['type'],
                    transaction['id']), tags=('shopping',))
                total_expense += float(transaction['amount'])

        # Fetch shopping list
        self.shopping_tree.delete(*self.shopping_tree.get_children())

        self.cursor.execute("SELECT * FROM shopping_list")
        shopping_list = self.cursor.fetchall()

        for index, shopping_item in enumerate(shopping_list):
            self.shopping_tree.insert("", "end",
                                      values=(index + 1, shopping_item['item'], shopping_item['price'],))

        # Fetch total income from database
        self.cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='Income'")
        total_income_row = self.cursor.fetchone()
        total_income = total_income_row['SUM(amount)'] if total_income_row['SUM(amount)'] else 0

        # Fetch total expense from database
        self.cursor.execute("SELECT SUM(amount) FROM transactions WHERE type= :type1 OR type= :type2",
                            {"type1": "Expence", "type2": "Shopping", })
        total_expense_row = self.cursor.fetchone()
        total_expense = total_expense_row['SUM(amount)'] if total_expense_row['SUM(amount)'] else 0

        # Update total income, total expenses, and net worth labels
        self.total_income_label.config(text=f"₺{total_income:.2f}" if total_income is not None else "₺0.00")
        self.total_expense_label.config(text=f"₺{total_expense:.2f}" if total_expense is not None else "₺0.00")
        self.net_worth_label.config(
            text=f"₺{total_income - total_expense:.2f}" if total_income is not None and total_expense is not None else "₺0.00")

        self.title_entry.grid_remove()  # Hide title entry
        self.title_combobox.grid(row=1, column=1, padx=5, pady=5, sticky='w')

    def remove_transaction(self):
        selected_items = self.transaction_table.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select an item to remove.")
            return

        for item in selected_items:
            transaction_id = self.transaction_table.item(item)['values'][4]
            self.cursor.execute("DELETE FROM transactions WHERE id=?", (transaction_id,))
            self.conn.commit()

        # Güncellenmiş verileri yükle
        self.load_initial_data()

    def clear_fields(self):
        self.transaction_type.set("")
        self.title_entry.delete(0, tk.END)
        self.amount_entry.delete(0, tk.END)

    def remove_shopping_item(self):
        selected_items = self.shopping_tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select an item to remove.")
            return

        for item in selected_items:
            item_name = self.shopping_tree.item(item, "values")[1]  # Get item name
            self.shopping_tree.delete(item)

            self.cursor.execute("DELETE FROM shopping_list WHERE item=?", (item_name,))
            self.conn.commit()

    def mark_as_purchased_shopping(self):
        selected_items = self.shopping_tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select an item to mark as purchased.")
            return

        for item in selected_items:
            item_id, item_name, item_amount = self.shopping_tree.item(item, "values")
            self.shopping_tree.delete(item)

            item_amount = item_amount[:-3].replace(".", "").replace(",", ".")
            print(item_amount)

            self.cursor.execute("DELETE FROM shopping_list WHERE item=?", (item_name,))
            self.cursor.execute("INSERT INTO transactions (date, description, amount, type) VALUES (?, ?, ?, ?)",
                                (datetime.now(), item_name, item_amount, "Shopping"))
            self.conn.commit()
            self.load_initial_data()

    def reset_monthly_transactions(self):
        # Get the reset day from the database
        reset_day = self.get_reset_day()

        # Check if today is the reset day
        today = datetime.now()
        if today.day == reset_day:
            # Get the first and last day of the month
            first_day = today.replace(day=1)
            last_day = today.replace(day=monthrange(today.year, today.month)[1])

            # Reset transactions table
            self.cursor.execute("DELETE FROM transactions WHERE date BETWEEN ? AND ?", (first_day, last_day))
            self.conn.commit()

            # Add a new transaction
            self.cursor.execute("INSERT INTO transactions (date, description, amount, type) VALUES (?, ?, ?, ?)",
                                (datetime.now(), "Increased Money", self.net_worth_label.cget("text")[1:], "Income"))
            self.conn.commit()

            # Load updated data
            self.load_initial_data()

    def get_reset_day(self):
        self.cursor.execute("SELECT value FROM settings WHERE name='monthly_transactions_reset_day'")
        row = self.cursor.fetchone()
        return int(row['value']) if row else None

    def set_default_monthly_transactions_day(self):
        today = datetime.now()
        default_day = today.day
        self.cursor.execute("INSERT OR IGNORE INTO settings (name, value) VALUES (?, ?)",
                            ('monthly_transactions_day', default_day))
        self.conn.commit()

    def get_saved_monthly_transactions_day(self):
        self.cursor.execute("SELECT value FROM settings WHERE name='monthly_transactions_day'")
        row = self.cursor.fetchone()
        return int(row['value']) if row else None

    def open_settings(self):
        self.settings_page = SettingsPage(tk.Toplevel(self.root), self)


class SettingsPage:
    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.root.title("Settings")
        self.theme = app.theme

        self.amazon_email_entry = ttk.Entry()
        self.amazon_pass_entry = ttk.Entry()
        self.email = tk.StringVar()
        self.password = tk.StringVar()
        self.linked_account = tk.StringVar()

        self.create_settings()

        self.app.cursor.execute("SELECT value FROM settings WHERE name='amazon_wishlist'")
        amazon_account = self.app.cursor.fetchone()

        if amazon_account['value']:
            self.linked_account = tk.StringVar(value="amazon_on")
            self.email = tk.StringVar(value=amazon_account['value'].split(",")[0])
            self.password = tk.StringVar(value=amazon_account['value'].split(",")[1])
        else:
            self.amazon_email_entry.grid_remove()
            self.amazon_pass_entry.grid_remove()

    def create_settings(self):
        # Create frame for settings
        frame = ttk.LabelFrame(self.root
                               , text="Settings")
        frame.pack(padx=10, pady=10)

        # Get the saved monthly_transactions_day value from the database
        saved_day = self.app.get_saved_monthly_transactions_day()

        self.create_link_wishlist(frame)

        ttk.Label(frame, text="Select Monthly Transactions Day:").grid(row=0, column=0, padx=5, pady=5)

        # Create a combobox widget to select day of the month
        self.day_combobox = ttk.Combobox(frame, values=[f"{i}. günü" for i in range(1, 32)])
        self.day_combobox.grid(row=0, column=1, padx=5, pady=5)

        # Set default value to saved day if it exists, otherwise set to 15th day of the month
        if saved_day is not None:
            self.day_combobox.set(f"{saved_day}. günü")
        else:
            self.day_combobox.set("15. günü")

        # Add a label for theme selection
        ttk.Label(frame, text="Select Theme:").grid(row=1, column=0, padx=5, pady=5)

        # Create a combobox widget to select theme
        self.theme_combobox = ttk.Combobox(frame, values=list(theme.capitalize() for theme in [
            "cerulean", "cosmo", "cyborg", "darkly",
            "flatly", "journal", "litera", "lumen",
            "minty", "pulse", "sandstone", "simplex",
            "solar", "spacelab", "superhero",
            "united", "yeti", "vapor"
        ]))
        self.theme_combobox.grid(row=1, column=1, padx=5, pady=5)

        self.theme_combobox.set(self.theme.capitalize())

        # Add a button to save the selected settings
        save_button = ttk.Button(frame, text="Save", command=self.save_settings)
        save_button.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

    def create_link_wishlist(self, root):
        wishlist_frame = ttk.LabelFrame(root, text="Link Wishlist")
        wishlist_frame.grid(row=2, columnspan=2, padx=10, pady=10, sticky="nsew")
        wishlist_frame.grid_columnconfigure(0, weight=1)

        def show_entries():
            print(self.linked_account.get())
            if self.linked_account.get() == "amazon_on":
                self.amazon_email_entry.grid(row=0, column=1, pady=5, padx=5)
                self.amazon_pass_entry.grid(row=0, column=2, pady=5, padx=5)
            if self.linked_account.get() == "amazon_off":
                self.amazon_email_entry.grid_remove()
                self.email = None
                self.amazon_pass_entry.grid_remove()
                self.password = None

        amazon_checkbox = ttk.Checkbutton(wishlist_frame, text="Amazon", variable=self.linked_account,
                                          onvalue="amazon_on",
                                          offvalue="amazon_off",
                                          bootstyle="round-toggle",
                                          command=show_entries)
        amazon_checkbox.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.amazon_email_entry = ttk.Entry(wishlist_frame, textvariable=self.email)
        self.amazon_email_entry.grid(row=0, column=1, pady=10, padx=5)
        self.amazon_pass_entry = ttk.Entry(wishlist_frame, textvariable=self.password)
        self.amazon_pass_entry.grid(row=0, column=2, pady=10, padx=5)

    def save_settings(self):
        selected_day = int(self.day_combobox.get().split('.')[0])
        selected_theme = self.theme_combobox.get().lower()
        if not self.amazon_email_entry.get() and self.amazon_pass_entry.get():
            amazon_account = None
        else:
            amazon_account = f"{self.amazon_email_entry.get()},{self.amazon_pass_entry.get()}"

        if selected_theme != self.theme:
            # Show warning message about theme change requiring a restart
            messagebox.showwarning("Warning", "Changing the theme requires restarting the application.")

            self.app.cursor.execute("UPDATE settings SET value=? WHERE name='theme'", (selected_theme,))
            self.app.cursor.execute("UPDATE settings SET value=? WHERE name='monthly_transactions_day'",
                                    (selected_day,))
            self.app.cursor.execute("UPDATE settings SET value=? WHERE name='amazon_wishlist'", (amazon_account,))
            self.app.conn.commit()
            # Restart the application with the new theme
            self.restart_program()

        else:
            self.app.cursor.execute("UPDATE settings SET value=? WHERE name='theme'", (selected_theme,))
            self.app.cursor.execute("UPDATE settings SET value=? WHERE name='monthly_transactions_day'",
                                    (selected_day,))
            self.app.cursor.execute("UPDATE settings SET value=? WHERE name='amazon_wishlist'", (amazon_account,))

            self.app.conn.commit()

        self
        self.root.destroy()

    def restart_program(self):
        self.root.destroy()
        python = sys.executable
        os.execl(python, python, *sys.argv)


# Custom row factory function to convert dates to datetime objects
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        if col[0] == 'date':
            d[col[0]] = datetime.fromisoformat(row[idx])
        else:
            d[col[0]] = row[idx]
    return d


def get_saved_theme():
    conn = sqlite3.connect('accounting.db')
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE name='theme'")
    row = cursor.fetchone()
    return row[0] if row else None


def get_amazon_wishlist(email, password):
    print("Thread starting")
    # Amazon hesabınıza giriş yapacak bilgileri girin

    # email = "erdemozbaykus@gmail.com"
    # password = "Erdem!2002"

    # Chrome tarayıcı seçeneklerini tanımla (gizli mod)
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    # chrome_options.add_experimental_option("detach", True)

    # Web sürücüsünü başlat
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1000, 1500)
    driver.set_window_position(1, 1)

    # Amazon.com.tr sayfasını aç
    driver.get("https://www.amazon.com.tr")

    # Giriş yap butonuna tıklamak için bekleme süresi ekle
    WebDriverWait(driver, 1000).until(EC.element_to_be_clickable((By.ID, "nav-link-accountList"))).click()

    # Email girişi
    print("Trying to connect")
    driver.find_element(By.ID, "ap_email").send_keys(email)
    driver.find_element(By.ID, "continue").click()
    time.sleep(2)

    # Şifre girişi
    driver.find_element(By.ID, "ap_password").send_keys(password)
    driver.find_element(By.ID, "signInSubmit").click()
    time.sleep(2)

    # Alışveriş listesine git
    print("Connected")
    driver.get("https://www.amazon.com.tr/gp/registry/wishlist")

    # Sayfanın HTML içeriğini al
    html = driver.page_source

    # BeautifulSoup kullanarak HTML'i parse et
    soup = BeautifulSoup(html, "html.parser")

    # Alışveriş listesi öğelerini bul
    items = soup.find_all("h2", class_="a-size-base")

    # Alışveriş listesi öğelerinin adlarını ve fiyatlarını yazdır
    wishlist = []
    for item in items:
        item_name = item.text.strip()
        item_price = item.find_next("span", class_="a-offscreen")
        if item_price:
            item_price = item_price.text.strip()
            wishlist.append({"item": item_name, "price": item_price})

    # Web sürücüsünü kapat
    driver.quit()
    print("Amazon wishlist data successfully initialized")
    return wishlist


def initialize_amazon_data(self):
    conn = sqlite3.connect('accounting.db')
    conn.row_factory = dict_factory  # Set custom row factory
    cursor = conn.cursor()

    cursor.execute("SELECT value FROM settings WHERE name='amazon_wishlist'")
    amazon_account = cursor.fetchone()

    if amazon_account['value']:
        try:
            email = amazon_account['value'].split(",")[0]
            password = amazon_account['value'].split(",")[1]
            wishlist = get_amazon_wishlist(email, password)
            for item in wishlist:
                item_name = item['item']
                item_price = item['price']
                print("items successfully got")

                # Öğenin veritabanında var olup olmadığını kontrol et
                cursor.execute("SELECT * FROM shopping_list WHERE item=?", (item_name,))
                existing_item = cursor.fetchone()

                cursor.execute("SELECT * FROM transactions WHERE type=:type AND description=:description",
                               {"type": 'Shopping', "description": item_name})
                existing_translation = cursor.fetchone()

                if existing_item or existing_translation:
                    # Öğe zaten varsa, fiyatını güncelle
                    cursor.execute("UPDATE shopping_list SET price=? WHERE item=?", (item_price, item_name))
                else:
                    # Öğe yoksa, yeni bir kayıt ekle
                    cursor.execute("INSERT INTO shopping_list (item, price) VALUES (?,?)",
                                   (item_name, item_price))

                conn.commit()
            return self.load_initial_data

        except Exception as e:
            messagebox.showerror("Error", "Amazon has been unreachable at this moment try again")
            print("Amazon has been unreachable \n", e)


def main():
    theme = get_saved_theme()
    root = ttk.Window(themename=theme)
    app = AccountingApp(root, theme)
    root.after(1)
    root.after(1000, app.reset_monthly_transactions)
    root.mainloop()


if __name__ == "__main__":
    main()
