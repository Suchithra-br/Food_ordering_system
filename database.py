import sqlite3
import json
import os
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "restaurant.db")
BILLS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bills.json")

# Default initial menu based on existing app.py
DEFAULT_MENU = [
    {"name": "Butter Chicken", "price": 220, "category": "Main Course", "emoji": "🍛", "is_veg": 0, "description": "Tender chicken cooked in rich buttery tomato gravy."},
    {"name": "Paneer Tikka", "price": 180, "category": "Starters", "emoji": "🧀", "is_veg": 1, "description": "Grilled cottage cheese cubes marinated in aromatic spices."},
    {"name": "Veg Biryani", "price": 160, "category": "Main Course", "emoji": "🍚", "is_veg": 1, "description": "Fragrant basmati rice layered with spiced fresh vegetables."},
    {"name": "Chicken Biryani", "price": 200, "category": "Main Course", "emoji": "🍗", "is_veg": 0, "description": "Authentic dum biryani prepared with tender spiced chicken."},
    {"name": "Masala Dosa", "price": 90, "category": "Starters", "emoji": "🥞", "is_veg": 1, "description": "Crispy fermented crepe filled with spiced potato masala."},
    {"name": "Samosa (2 pcs)", "price": 40, "category": "Starters", "emoji": "🥟", "is_veg": 1, "description": "Flaky golden pastry filled with spiced potato and peas."},
    {"name": "Gulab Jamun", "price": 60, "category": "Desserts", "emoji": "🍩", "is_veg": 1, "description": "Soft milk-solid dumplings soaked in warm rose syrup."},
    {"name": "Mango Lassi", "price": 70, "category": "Beverages", "emoji": "🥤", "is_veg": 1, "description": "Refreshing chilled yogurt smoothie blended with sweet mango."},
    {"name": "Masala Chai", "price": 30, "category": "Beverages", "emoji": "☕", "is_veg": 1, "description": "Traditional Indian spiced milk tea brewed with cardamom & ginger."},
    {"name": "Cold Coffee", "price": 80, "category": "Beverages", "emoji": "🧋", "is_veg": 1, "description": "Rich iced blended coffee topped with frothy cream."},
    {"name": "Naan", "price": 35, "category": "Breads", "emoji": "🫓", "is_veg": 1, "description": "Soft and fluffy traditional tandoori flatbread."},
    {"name": "Garlic Naan", "price": 45, "category": "Breads", "emoji": "🧄", "is_veg": 1, "description": "Clay oven flatbread infused with roasted garlic and butter."},
    {"name": "Dal Tadka", "price": 120, "category": "Main Course", "emoji": "🍲", "is_veg": 1, "description": "Yellow lentils tempered with ghee, cumin, garlic, and chilies."},
    {"name": "Raita", "price": 40, "category": "Sides", "emoji": "🥣", "is_veg": 1, "description": "Cool seasoned yogurt with cucumber, roasted cumin, and herbs."},
    {"name": "Ice Cream", "price": 50, "category": "Desserts", "emoji": "🍨", "is_veg": 1, "description": "Delicious creamy dessert scoop in classic vanilla or chocolate."},
]


def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes tables and migrates existing bills.json data seamlessly."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Menu Items Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            emoji TEXT DEFAULT '🍽️',
            is_veg INTEGER DEFAULT 1,
            description TEXT DEFAULT '',
            is_available INTEGER DEFAULT 1
        )
    """)

    # 2. Orders Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_no INTEGER UNIQUE NOT NULL,
            table_number INTEGER DEFAULT 1,
            customer_name TEXT DEFAULT 'Guest',
            customer_phone TEXT DEFAULT '',
            order_type TEXT DEFAULT 'Dine-in',
            items_json TEXT NOT NULL,
            subtotal REAL NOT NULL,
            tax REAL DEFAULT 0.0,
            total REAL NOT NULL,
            status TEXT DEFAULT 'Placed',
            time TEXT NOT NULL,
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # Pre-populate menu if empty
    cursor.execute("SELECT COUNT(*) FROM menu_items")
    if cursor.fetchone()[0] == 0:
        for item in DEFAULT_MENU:
            cursor.execute("""
                INSERT INTO menu_items (name, category, price, emoji, is_veg, description, is_available)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (item["name"], item["category"], item["price"], item["emoji"], item["is_veg"], item["description"]))
        conn.commit()

    # Migrate existing bills from bills.json if orders table is empty
    cursor.execute("SELECT COUNT(*) FROM orders")
    if cursor.fetchone()[0] == 0 and os.path.exists(BILLS_FILE):
        try:
            with open(BILLS_FILE, "r") as f:
                bills = json.load(f)
            for i, bill in enumerate(bills):
                bill_no = bill.get("bill_no", i + 1)
                table = bill.get("table", 1)
                try:
                    table_num = int(table) if str(table).isdigit() else 1
                except:
                    table_num = 1
                items = bill.get("items", [])
                total = bill.get("total", 0)
                subtotal = total
                time_str = bill.get("time", datetime.now().strftime("%d-%m-%Y %I:%M %p"))
                cursor.execute("""
                    INSERT OR IGNORE INTO orders (bill_no, table_number, customer_name, order_type, items_json, subtotal, tax, total, status, time)
                    VALUES (?, ?, 'Guest', 'Dine-in', ?, ?, 0.0, ?, 'Served', ?)
                """, (bill_no, table_num, json.dumps(items), subtotal, total, time_str))
            conn.commit()
        except Exception as e:
            print(f"Notice: Migration of bills.json skipped or partially succeeded: {e}")

    conn.close()


# Initialize on import
init_db()


# ================= MENU OPERATIONS =================
def get_all_menu_items(active_only=False):
    conn = get_connection()
    cursor = conn.cursor()
    if active_only:
        cursor.execute("SELECT * FROM menu_items WHERE is_available = 1 ORDER BY category, name")
    else:
        cursor.execute("SELECT * FROM menu_items ORDER BY category, name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_menu_categories():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM menu_items ORDER BY category")
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()
    return categories


def add_menu_item(name, category, price, emoji="🍽️", is_veg=1, description=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO menu_items (name, category, price, emoji, is_veg, description, is_available)
        VALUES (?, ?, ?, ?, ?, ?, 1)
    """, (name.strip(), category.strip(), float(price), emoji.strip() or "🍽️", int(is_veg), description.strip()))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def update_menu_item(item_id, name, category, price, emoji, is_veg, description, is_available):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE menu_items
        SET name = ?, category = ?, price = ?, emoji = ?, is_veg = ?, description = ?, is_available = ?
        WHERE id = ?
    """, (name.strip(), category.strip(), float(price), emoji.strip() or "🍽️", int(is_veg), description.strip(), int(is_available), item_id))
    conn.commit()
    conn.close()


def delete_menu_item(item_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM menu_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


def toggle_item_availability(item_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE menu_items SET is_available = CASE WHEN is_available = 1 THEN 0 ELSE 1 END WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


# ================= ORDER OPERATIONS =================
def get_next_bill_no():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(MAX(bill_no), 0) + 1 FROM orders")
    next_no = cursor.fetchone()[0]
    conn.close()
    return next_no


def create_order(table_number, items, subtotal, tax=0.0, total=None, customer_name="Guest", customer_phone="", order_type="Dine-in", notes=""):
    if total is None:
        total = round(subtotal + tax, 2)
    bill_no = get_next_bill_no()
    time_str = datetime.now().strftime("%d-%m-%Y %I:%M %p")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO orders (bill_no, table_number, customer_name, customer_phone, order_type, items_json, subtotal, tax, total, status, time, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Placed', ?, ?)
    """, (bill_no, int(table_number), customer_name.strip() or "Guest", customer_phone.strip(), order_type, json.dumps(items), float(subtotal), float(tax), float(total), time_str, notes.strip()))
    conn.commit()
    conn.close()

    # Backward compatibility: Sync with bills.json safely
    sync_to_bills_json()

    return bill_no


def get_all_orders(status_filter=None):
    conn = get_connection()
    cursor = conn.cursor()
    if status_filter and status_filter != "All":
        cursor.execute("SELECT * FROM orders WHERE status = ? ORDER BY id DESC", (status_filter,))
    else:
        cursor.execute("SELECT * FROM orders ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    orders = []
    for row in rows:
        order = dict(row)
        try:
            order["items"] = json.loads(order["items_json"])
        except:
            order["items"] = []
        orders.append(order)
    return orders


def get_orders_by_table(table_number):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE table_number = ? ORDER BY id DESC", (int(table_number),))
    rows = cursor.fetchall()
    conn.close()
    orders = []
    for row in rows:
        order = dict(row)
        try:
            order["items"] = json.loads(order["items_json"])
        except:
            order["items"] = []
        orders.append(order)
    return orders


def get_order_by_bill_no(bill_no):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE bill_no = ?", (int(bill_no),))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    order = dict(row)
    try:
        order["items"] = json.loads(order["items_json"])
    except:
        order["items"] = []
    return order


def update_order_status(bill_no, new_status):
    valid_statuses = ["Placed", "Preparing", "Ready", "Served", "Cancelled"]
    if new_status not in valid_statuses:
        return False
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = ? WHERE bill_no = ?", (new_status, int(bill_no)))
    conn.commit()
    conn.close()

    sync_to_bills_json()
    return True


def get_order_statistics():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*), COALESCE(SUM(total), 0) FROM orders WHERE status != 'Cancelled'")
    total_orders, total_revenue = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) FROM orders WHERE status IN ('Placed', 'Preparing')")
    active_orders = cursor.fetchone()[0]

    # Today's date prefix
    today_prefix = datetime.now().strftime("%d-%m-%Y")
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(total), 0) FROM orders WHERE time LIKE ? AND status != 'Cancelled'", (f"{today_prefix}%",))
    today_orders, today_revenue = cursor.fetchone()

    conn.close()

    return {
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "active_orders": active_orders,
        "today_orders": today_orders,
        "today_revenue": round(today_revenue, 2)
    }


# ================= BACKWARD COMPATIBILITY HELPERS =================
def sync_to_bills_json():
    """Keeps bills.json updated so legacy scripts/CLI stay fully compatible."""
    try:
        orders = get_all_orders()
        bills_data = []
        for o in reversed(orders):
            bills_data.append({
                "bill_no": o["bill_no"],
                "table": o["table_number"],
                "items": o["items"],
                "total": o["total"],
                "time": o["time"],
                "status": o.get("status", "Placed"),
                "customer": o.get("customer_name", "Guest")
            })
        temp_file = BILLS_FILE + ".tmp"
        with open(temp_file, "w") as f:
            json.dump(bills_data, f, indent=2)
        os.replace(temp_file, BILLS_FILE)
    except Exception as e:
        print(f"Warning: Failed to sync bills.json: {e}")


def load_bills():
    """Matches the original signature in app.py and food.py."""
    orders = get_all_orders()
    bills = []
    for o in reversed(orders):
        bills.append({
            "bill_no": o["bill_no"],
            "table": o["table_number"],
            "items": o["items"],
            "total": o["total"],
            "time": o["time"],
            "status": o.get("status", "Placed"),
            "customer_name": o.get("customer_name", "Guest")
        })
    return bills


def save_bill(bill):
    """Matches original save_bill signature from app.py / food.py."""
    table = bill.get("table", 1)
    try:
        table_num = int(table) if str(table).isdigit() else 1
    except:
        table_num = 1
    items = bill.get("items", [])
    total = bill.get("total", 0)
    customer = bill.get("customer_name", "Guest")
    create_order(
        table_number=table_num,
        items=items,
        subtotal=total,
        tax=0.0,
        total=total,
        customer_name=customer
    )
