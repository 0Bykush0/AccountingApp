import tkinter as tk
from calendar import monthrange
from tkinter import ttk
from tkinter import messagebox, simpledialog
import sqlite3
from datetime import datetime

from tkcalendar import DateEntry


# Custom row factory function to convert dates to datetime objects
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        if col[0] == 'date':
            d[col[0]] = datetime.fromisoformat(row[idx])
        else:
            d[col[0]] = row[idx]
    return d


class AccountingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Accounting App")

        # Initialize database
        self.conn = sqlite3.connect('accounting.db')
        self.conn.row_factory = dict_factory  # Set custom row factory
        self.cursor = self.conn.cursor()
        self.create_tables()

        # Initialize variables
        self.transaction_type = tk.StringVar()

        # Create GUI
        self.create_income_expense_widgets()
        self.create_income_expense_table()
        self.create_shopping_page()

        # Set default monthly transactions date
        self.set_default_monthly_transactions_day()

        # Gizli başlat
        self.title_entry.grid_remove()  # Title entry'yi gizle

        # Load initial data
        self.load_initial_data()

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
                            amount REAL)''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS settings
                                (name TEXT PRIMARY KEY,
                                value TEXT)''')

        self.conn.commit()

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

    def save_monthly_transactions_day(self, selected_day):
        self.cursor.execute("UPDATE settings SET value=? WHERE name='monthly_transactions_day'", (selected_day,))
        self.conn.commit()

    def open_settings(self):
        self.settings_page = SettingsPage(tk.Toplevel(self.root), self)

    def create_income_expense_widgets(self):
        frame = ttk.LabelFrame(self.root, text="Income & Expenses")
        frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        # Make frame fill available horizontal space
        frame.grid_columnconfigure(0, weight=1)

        income_checkbox = ttk.Checkbutton(frame, text="Income", variable=self.transaction_type, onvalue="Income",
                                          offvalue="")
        income_checkbox.grid(row=0, column=0, sticky='w')

        expense_checkbox = ttk.Checkbutton(frame, text="Expense", variable=self.transaction_type, onvalue="Expense",
                                           offvalue="")
        expense_checkbox.grid(row=0, column=1, sticky='w')

        self.title_label = ttk.Label(frame, text="Title:")
        self.title_label.grid(row=1, column=0, sticky='w')

        items = ['Harçlık', 'Burs', 'Abonelik', 'Borç', 'Yeme-İçme', 'Hediye', 'Others']
        self.title_combobox = ttk.Combobox(frame, state="readonly", values=items, )
        self.title_combobox.grid(row=1, column=1, padx=5, pady=5, sticky='e')
        self.title_combobox.bind("<<ComboboxSelected>>", self.on_combobox_select)

        self.title_entry = ttk.Entry(frame, width=14)
        self.title_entry.grid(row=1, column=1, padx=5, pady=5, sticky='e')

        self.amount_label = ttk.Label(frame, text="Amount:")
        self.amount_label.grid(row=2, column=0, sticky='w')
        self.amount_entry = ttk.Entry(frame, width=20)
        self.amount_entry.grid(row=2, column=1, padx=5, pady=5, sticky='ew')

        self.submit_button = ttk.Button(frame, text="Submit", command=self.add_transaction)
        self.submit_button.grid(row=3, column=1, columnspan=1, pady=10, padx=5, sticky='ew')

        self.refresh_button = ttk.Button(frame, text="Refresh", command=self.load_initial_data)
        self.refresh_button.grid(row=3, column=0, pady=10, padx=5, sticky='ew')

        # Add labels for total income, total expenses, and net worth
        ttk.Label(frame, text="Total Income:").grid(row=4, column=0, sticky='w')
        self.total_income_label = ttk.Label(frame, text="")
        self.total_income_label.grid(row=4, column=1, sticky='w')

        ttk.Label(frame, text="Total Expenses:").grid(row=5, column=0, sticky='w')
        self.total_expense_label = ttk.Label(frame, text="")
        self.total_expense_label.grid(row=5, column=1, sticky='w')

        ttk.Label(frame, text="Net Worth:").grid(row=6, column=0, sticky='w')
        self.net_worth_label = ttk.Label(frame, text="")
        self.net_worth_label.grid(row=6, column=1, sticky='w')

        # Create settings button
        self.settings_button = ttk.Button(frame, text="Settings", command=self.open_settings)
        self.settings_button.grid(row=7, column=0, padx=5, pady=5)

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
        self.transaction_table.heading("ID", text="ID", anchor=tk.W)  # Hide this column heading
        self.transaction_table.column("ID", width=0, stretch=tk.NO)  # Hide this column

        self.transaction_table.grid(row=0, column=0, sticky='nsew')

        # Make treeview expand to fill available space
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        # Add remove button
        remove_button = ttk.Button(frame, text="Remove", command=self.remove_transaction)
        remove_button.grid(row=1, column=0, pady=5)

        # Add this line to check if the button is enabled/disabled based on selection
        self.transaction_table.bind("<ButtonRelease-1>", lambda event: remove_button.config(
            state=tk.NORMAL) if self.transaction_table.selection() else remove_button.config(state=tk.DISABLED))

    def create_shopping_page(self):
        frame = ttk.LabelFrame(self.root, text="Shopping List")
        frame.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')

        # Make frame fill available horizontal space
        frame.grid_columnconfigure(0, weight=1)

        self.shopping_tree = ttk.Treeview(frame, columns=("Name", "Price"), show="headings")
        self.shopping_tree.heading("Name", text="Name")
        self.shopping_tree.heading("Price", text="Price")
        self.shopping_tree.column("Name", width=100)
        self.shopping_tree.column("Price", width=100)
        self.shopping_tree.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')

        # Create a frame for buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=1, column=0, pady=5, sticky='ew')

        # Add item button for shopping list
        add_item_button = ttk.Button(button_frame, text="Add Item", command=self.add_shopping_item)
        add_item_button.grid(row=0, column=0, padx=5, sticky='ew')

        # Add remove button for shopping list
        remove_shopping_button = ttk.Button(button_frame, text="Remove", command=self.remove_shopping_item)
        remove_shopping_button.grid(row=0, column=1, padx=5, sticky='ew')

        # Add mark as purchased button for shopping list
        mark_purchased_button = ttk.Button(button_frame, text="Mark as Purchased",
                                           command=self.mark_as_purchased_shopping)
        mark_purchased_button.grid(row=0, column=2, padx=5, sticky='ew')

        # Center the button frame horizontally
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)

    def on_combobox_select(self, event):
        selected_title = self.title_combobox.get()
        if selected_title == "Others":
            self.title_entry.delete(0, tk.END)  # Entry'yi temizle
            self.title_combobox.grid_remove()  # ComboBox'ı gizle
            self.title_entry.grid(row=1, column=1, padx=5, pady=5, sticky='ew')  # Title entry'yi göster
        else:
            self.title_entry.grid_remove()  # Title entry'yi gizle
            self.title_combobox.grid(row=1, column=1, padx=5, pady=5, sticky='w')  # ComboBox'ı göster
            if selected_title:
                if self.title_entry.get():
                    self.title_entry.insert(tk.END, f" ({selected_title})")
                else:
                    self.title_entry.insert(tk.END, selected_title)

    def add_transaction(self):
        transaction_type = self.transaction_type.get()
        title = self.title_entry.get()
        amount = self.amount_entry.get()

        # Check if title entry is empty, if so, switch back to combobox
        if not title and self.title_combobox.get() == 'Others':
            self.title_entry.grid_remove()  # Hide title entry
            self.title_combobox.grid(row=1, column=1, padx=5, pady=5, sticky='w')  # Show combobox

        if not (transaction_type and (
                title or (self.title_combobox.get() and self.title_combobox.get() != 'Others')) and amount):
            messagebox.showwarning("Warning", "Please fill in all fields.")
            return

        self.cursor.execute("INSERT INTO transactions (date, description, amount, type) VALUES (?, ?, ?, ?)",
                            (datetime.now(), title or self.title_combobox.get(), amount, transaction_type))
        self.conn.commit()

        # Güncellenmiş verileri yükle
        self.load_initial_data()
        self.clear_fields()

    def load_initial_data(self):
        self.transaction_table.delete(*self.transaction_table.get_children())

        # Fetch transactions from database
        self.cursor.execute("SELECT * FROM transactions")
        transactions = self.cursor.fetchall()

        total_income = 0
        total_expense = 0

        # Iterate over fetched transactions
        for transaction in transactions:
            formatted_date = transaction['date'].strftime('%Y-%m-%d')
            self.transaction_table.insert("", "end", values=(
                formatted_date, transaction['description'], transaction['amount'], transaction['type'],
                transaction['id']))

            # Calculate total income and total expense
            if transaction['type'] == 'Income':
                total_income += transaction['amount']
            elif transaction['type'] == 'Expense':
                total_expense += transaction['amount']

        # Fetch total income from database
        self.cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='Income'")
        total_income_row = self.cursor.fetchone()
        total_income = total_income_row['SUM(amount)'] if total_income_row else 0

        # Fetch total expense from database
        self.cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='Expense'")
        total_expense_row = self.cursor.fetchone()
        total_expense = total_expense_row['SUM(amount)'] if total_expense_row else 0

        # Update total income, total expenses, and net worth labels
        # Update total income, total expenses, and net worth labels
        self.total_income_label.config(text=f"₺{total_income:.2f}" if total_income is not None else "₺0.00")
        self.total_expense_label.config(text=f"₺{total_expense:.2f}" if total_expense is not None else "₺0.00")
        self.net_worth_label.config(
            text=f"₺{total_income - total_expense:.2f}" if total_income is not None and total_expense is not None else "₺0.00")

        self.title_entry.grid_remove()  # Hide title entry
        self.title_combobox.grid(row=1, column=1, padx=5, pady=5, sticky='w')

    def remove_transaction(self):
        selected_item = self.transaction_table.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select an item to remove.")
            return

        transaction_id = self.transaction_table.item(selected_item)['values'][4]
        self.cursor.execute("DELETE FROM transactions WHERE id=?", (transaction_id,))
        self.conn.commit()

        # Güncellenmiş verileri yükle
        self.load_initial_data()

    def clear_fields(self):
        self.transaction_type.set("")
        self.title_entry.delete(0, tk.END)
        self.amount_entry.delete(0, tk.END)

    def add_shopping_item(self):
        item = simpledialog.askstring("Add Shopping Item", "Enter item name:")
        if item:
            amount = simpledialog.askfloat("Add Shopping Item", f"Enter amount for {item}:")
            if amount is not None:
                self.shopping_tree.insert("", "end", values=(item, amount))

                self.cursor.execute("INSERT INTO shopping_list (item, amount) VALUES (?, ?)", (item, amount))
                self.conn.commit()

    def remove_shopping_item(self):
        selected_items = self.shopping_tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select an item to remove.")
            return

        for item in selected_items:
            item_name = self.shopping_tree.item(item, "values")[0]  # Get item name
            self.shopping_tree.delete(item)

            self.cursor.execute("DELETE FROM shopping_list WHERE item=?", (item_name,))
            self.conn.commit()

    def mark_as_purchased_shopping(self):
        selected_items = self.shopping_tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select an item to mark as purchased.")
            return

        for item in selected_items:
            item_name, item_amount = self.shopping_tree.item(item, "values")
            self.shopping_tree.delete(item)

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


class SettingsPage:
    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.root.title("Settings")

        # Create frame for settings
        frame = ttk.LabelFrame(root, text="Monthly Transactions Date")
        frame.pack(padx=10, pady=10)

        # Get the saved monthly_transactions_day value from the database
        saved_day = self.app.get_saved_monthly_transactions_day()

        # Create a combobox widget to select day of the month
        self.day_combobox = ttk.Combobox(frame, values=[f"{i}. günü" for i in range(1, 32)])
        self.day_combobox.grid(row=0, column=0, padx=5, pady=5)

        # Set default value to saved day if it exists, otherwise set to 15th day of the month
        if saved_day is not None:
            self.day_combobox.set(f"{saved_day}. günü")
        else:
            self.day_combobox.set("15. günü")

        # Add a button to save the selected day
        save_button = ttk.Button(frame, text="Save", command=self.save_day)
        save_button.grid(row=0, column=1, padx=5, pady=5)

    def save_day(self):
        selected_day = int(self.day_combobox.get().split('.')[0])
        self.app.save_monthly_transactions_day(selected_day)
        messagebox.showinfo("Success", "Monthly transactions day saved successfully.")
        self.root.destroy()  # Ayarlar penceresini kapat


def main():
    root = tk.Tk()
    app = AccountingApp(root)
    root.after(1000, app.reset_monthly_transactions)
    root.mainloop()


if __name__ == "__main__":
    main()
