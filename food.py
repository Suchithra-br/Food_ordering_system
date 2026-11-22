import json
import os
from datetime import datetime
try:
    import database
except ImportError:
    database = None

BILLS_FILE = "bills.json"

# ================= MENU =================
def get_current_menu():
    if database:
        items = database.get_all_menu_items(active_only=True)
        if items:
            return items
    # Fallback to default menu
    return [
        {"id": 1, "name": "Butter Chicken", "price": 220},
        {"id": 2, "name": "Paneer Tikka", "price": 180},
        {"id": 3, "name": "Veg Biryani", "price": 160},
        {"id": 4, "name": "Chicken Biryani", "price": 200},
        {"id": 5, "name": "Masala Dosa", "price": 90},
        {"id": 6, "name": "Samosa", "price": 40},
        {"id": 7, "name": "Gulab Jamun", "price": 60},
        {"id": 8, "name": "Mango Lassi", "price": 70}
    ]

# ================= FILE FUNCTIONS =================
def load_bills():
    if database:
        return database.load_bills()
    if os.path.exists(BILLS_FILE):
        try:
            with open(BILLS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_bill(bill):
    if database:
        database.save_bill(bill)
    else:
        bills = load_bills()
        bills.append(bill)
        with open(BILLS_FILE, "w") as f:
            json.dump(bills, f, indent=2)

# ================= DISPLAY MENU =================
def show_menu():
    menu = get_current_menu()
    print("\n========== MENU ==========")
    for item in menu:
        emoji = item.get("emoji", "")
        category = f"[{item.get('category')}] " if "category" in item else ""
        print(f"{item['id']}. {emoji} {item['name']} {category}- ₹{item['price']}")
    print("==========================")

# ================= ORDER FUNCTION =================
def order_food():
    menu = get_current_menu()
    menu_dict = {item["id"]: item for item in menu}
    cart = {}

    try:
        table_input = input("Enter Table Number: ").strip()
        table_number = int(table_input) if table_input.isdigit() else 1
    except Exception:
        table_number = 1

    while True:
        show_menu()
        choice = input("Enter item ID to add (or 'done' to finish): ").strip()

        if choice.lower() == "done":
            break

        if not choice.isdigit():
            print("Invalid item ID! Please enter a number or 'done'.")
            continue

        item_id = int(choice)
        if item_id not in menu_dict:
            print(f"Item ID {item_id} not found on menu.")
            continue

        try:
            qty_input = input("Enter quantity: ").strip()
            qty = int(qty_input)
            if qty <= 0:
                print("Quantity must be at least 1.")
                continue
        except ValueError:
            print("Invalid quantity. Please enter a valid number.")
            continue

        cart[item_id] = cart.get(item_id, 0) + qty

    if not cart:
        print("No items selected.")
        return

    print("\n===== YOUR ORDER =====")
    total = 0
    cart_items = []

    for item_id, qty in cart.items():
        item = menu_dict[item_id]
        subtotal = item["price"] * qty
        total += subtotal

        cart_items.append({
            "name": item["name"],
            "qty": qty,
            "price": item["price"],
            "subtotal": subtotal
        })

        print(f"{item['name']} x{qty} = ₹{subtotal}")

    print("----------------------")
    print(f"TOTAL = ₹{total}")

    confirm = input("Confirm order? (y/n): ").strip()

    if confirm.lower() == "y":
        bill = {
            "table": table_number,
            "items": cart_items,
            "total": total,
            "time": datetime.now().strftime("%d-%m-%Y %I:%M %p"),
            "bill_no": len(load_bills()) + 1
        }
        save_bill(bill)
        print("✅ Order Confirmed!")
    else:
        print("❌ Order Cancelled.")

# ================= ADMIN VIEW =================
def view_bills():
    bills = load_bills()

    if not bills:
        print("No bills found.")
        return

    print("\n======= ALL BILLS =======")
    for bill in bills:
        print(f"\nBill No: {bill.get('bill_no', 'N/A')}")
        print(f"Table: {bill.get('table', 'N/A')}")
        print(f"Time: {bill.get('time', 'N/A')}")
        print(f"Status: {bill.get('status', 'Placed')}")
        print("----------------------")
        for item in bill.get("items", []):
            print(f"{item.get('name', 'Item')} x{item.get('qty', 1)} = ₹{item.get('subtotal', 0)}")
        print("----------------------")
        print(f"Total: ₹{bill.get('total', 0)}")

# ================= MAIN MENU =================
def main():
    while True:
        print("\n====== AURELIUS ======")
        print("1. Order Food")
        print("2. View Bills (Admin)")
        print("3. Exit")

        choice = input("Enter choice: ").strip()

        if choice == "1":
            order_food()
        elif choice == "2":
            view_bills()
        elif choice == "3":
            print("Thank you!")
            break
        else:
            print("Invalid choice!")

# ================= RUN =================
if __name__ == "__main__":
    main()
