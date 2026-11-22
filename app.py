import streamlit as st
import json
import os
import hashlib
import hmac
import re
from datetime import datetime
import pandas as pd
import database

# ================= PASSWORD SECURITY (SALTED PBKDF2) =================
def hash_password(password: str, salt: bytes = None) -> str:
    """Derives a salted cryptographic key using 100,000 rounds of PBKDF2-HMAC-SHA256."""
    if salt is None:
        salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return salt.hex() + "$" + key.hex()


def verify_password(stored_hash: str, password_attempt: str) -> bool:
    """Verifies a password against a stored salt$key hash using constant-time comparison."""
    try:
        salt_hex, key_hex = stored_hash.split("$")
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        new_key = hashlib.pbkdf2_hmac("sha256", password_attempt.encode("utf-8"), salt, 100000)
        return hmac.compare_digest(key, new_key)
    except Exception:
        return False

# ================= CONFIGURATION & STYLING =================
st.set_page_config(
    page_title="Aurelius - Restaurant Ordering System",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern visual polish and responsive typography
st.markdown("""
<style>
    /* Card Styles */
    .menu-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 14px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .menu-card:hover {
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
    }
    
    /* Badges */
    .badge-veg {
        display: inline-block;
        background-color: #ecfdf5;
        color: #065f46;
        border: 1px solid #10b981;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .badge-nonveg {
        display: inline-block;
        background-color: #fef2f2;
        color: #991b1b;
        border: 1px solid #ef4444;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .badge-category {
        display: inline-block;
        background-color: #f1f5f9;
        color: #475569;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    .badge-status-placed {
        background-color: #fef3c7;
        color: #92400e;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
    }
    .badge-status-preparing {
        background-color: #e0e7ff;
        color: #3730a3;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
    }
    .badge-status-ready {
        background-color: #fce7f3;
        color: #9d174d;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
    }
    .badge-status-served {
        background-color: #d1fae5;
        color: #065f46;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
    }
    .badge-status-cancelled {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
    }
    
    /* Order summary receipt */
    .receipt-box {
        background-color: #f8fafc;
        border: 1px dashed #cbd5e1;
        border-radius: 10px;
        padding: 18px;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)


# ================= SESSION STATE INITIALIZATION =================
if "cart" not in st.session_state:
    st.session_state.cart = {}  # {item_id: quantity}

if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

if "last_order_bill_no" not in st.session_state:
    st.session_state.last_order_bill_no = None

# Salted PBKDF2 default admin credentials (admin / admin123)
DEFAULT_SALT = bytes.fromhex("e3b0c44298fc1c149afbf4c8996fb924")
DEFAULT_ADMIN_HASH = hash_password("admin123", salt=DEFAULT_SALT)

ADMIN_USER = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", DEFAULT_ADMIN_HASH)


# ================= CART FUNCTIONS =================
def add_item(item_id):
    st.session_state.cart[item_id] = 1


def increment(item_id):
    st.session_state.cart[item_id] = st.session_state.cart.get(item_id, 0) + 1


def decrement(item_id):
    qty = st.session_state.cart.get(item_id, 0)
    if qty <= 1:
        st.session_state.cart.pop(item_id, None)
    else:
        st.session_state.cart[item_id] -= 1


def clear_cart():
    st.session_state.cart = {}


# ================= SIDEBAR NAVIGATION =================
st.sidebar.markdown("## 🍽️ Aurelius Dining")
nav_choice = st.sidebar.radio(
    "Navigation",
    ["🍽️ Order Food", "🔍 Track Order", "🧾 Admin Panel"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("💡 **Tip:** Table QR ordering made simple. Track active orders in real-time.")


# ==============================================================================
# 1. ORDER FOOD (CUSTOMER MENU & CHECKOUT)
# ==============================================================================
if nav_choice == "🍽️ Order Food":
    st.markdown("<h1 style='text-align:center; color:#1e293b;'>🍽️ Aurelius</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#64748b; font-size:1.1rem; margin-top:-10px;'>Authentic Flavors, Made Fresh to Order</p>", unsafe_allow_html=True)

    # Top Dining Preferences Bar
    with st.container():
        st.markdown("### 📋 Table & Dining Details")
        c1, c2, c3, c4 = st.columns([1.5, 2, 2, 2])
        with c1:
            table_number = st.number_input("Table No.", min_value=1, step=1, value=1, help="Your table number in the restaurant")
        with c2:
            customer_name = st.text_input("Your Name", value="Guest", placeholder="e.g. Rahul Sharma")
        with c3:
            customer_phone = st.text_input("Phone (Optional)", placeholder="e.g. 9876543210")
        with c4:
            order_type = st.selectbox("Order Type", ["Dine-in", "Takeaway"])

    st.markdown("---")

    # Fetch Menu Items from Database
    all_menu = database.get_all_menu_items()
    categories = ["All"] + database.get_menu_categories()

    # Search & Filter Row
    col_search, col_cat, col_diet = st.columns([2.5, 1.5, 1.2])
    with col_search:
        search_query = st.text_input("🔍 Search food items...", placeholder="Search by dish name, keyword...").strip().lower()
    with col_cat:
        selected_category = st.selectbox("Category", categories, index=0)
    with col_diet:
        dietary_filter = st.selectbox("Dietary", ["All", "🟢 Veg Only", "🔴 Non-Veg Only"], index=0)

    # Filter Items
    filtered_menu = []
    for item in all_menu:
        # Category check
        if selected_category != "All" and item["category"] != selected_category:
            continue
        # Search query check
        if search_query and (search_query not in item["name"].lower() and search_query not in item["description"].lower()):
            continue
        # Dietary check
        if dietary_filter == "🟢 Veg Only" and item["is_veg"] != 1:
            continue
        if dietary_filter == "🔴 Non-Veg Only" and item["is_veg"] == 1:
            continue
        filtered_menu.append(item)

    # Main Content Columns: Menu on Left (65%), Cart on Right (35%)
    menu_col, cart_col = st.columns([1.8, 1.2])

    with menu_col:
        st.markdown(f"### 📜 Menu Items ({len(filtered_menu)} dishes)")

        if not filtered_menu:
            st.warning("No dishes match your search or filter criteria. Try selecting another category!")
        else:
            for item in filtered_menu:
                is_available = bool(item.get("is_available", 1))
                is_veg = bool(item.get("is_veg", 1))
                diet_badge = '<span class="badge-veg">🟢 VEG</span>' if is_veg else '<span class="badge-nonveg">🔴 NON-VEG</span>'
                cat_badge = f'<span class="badge-category">{item["category"]}</span>'

                with st.container():
                    col_info, col_action = st.columns([3, 1.2])

                    with col_info:
                        st.markdown(
                            f"**{item['emoji']} {item['name']}** — **₹{item['price']:.0f}** {diet_badge} {cat_badge}",
                            unsafe_allow_html=True
                        )
                        if item.get("description"):
                            st.caption(item["description"])

                    with col_action:
                        if not is_available:
                            st.markdown("<span style='color:#ef4444; font-size:0.85rem; font-weight:600;'>Sold Out</span>", unsafe_allow_html=True)
                        else:
                            qty = st.session_state.cart.get(item["id"], 0)
                            if qty == 0:
                                st.button("Add +", key=f"add_{item['id']}", on_click=add_item, args=(item["id"],), use_container_width=True)
                            else:
                                b_dec, b_qty, b_inc = st.columns([1, 1.2, 1])
                                with b_dec:
                                    st.button("➖", key=f"dec_{item['id']}", on_click=decrement, args=(item["id"],))
                                with b_qty:
                                    st.markdown(f"<div style='text-align:center; font-weight:bold; padding-top:6px;'>{qty}</div>", unsafe_allow_html=True)
                                with b_inc:
                                    st.button("➕", key=f"inc_{item['id']}", on_click=increment, args=(item["id"],))

                    st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid #f1f5f9;'>", unsafe_allow_html=True)

    # Cart Column
    with cart_col:
        st.markdown("### 🛒 Your Order Cart")

        if not st.session_state.cart:
            st.info("Your cart is empty. Click **Add +** on any dish to start your order!")
        else:
            subtotal = 0
            cart_items_data = []
            menu_lookup = {item["id"]: item for item in all_menu}

            for item_id, qty in list(st.session_state.cart.items()):
                if item_id not in menu_lookup:
                    continue
                item = menu_lookup[item_id]
                item_subtotal = item["price"] * qty
                subtotal += item_subtotal

                c_name, c_sub = st.columns([2.5, 1.5])
                with c_name:
                    st.write(f"{item['emoji']} {item['name']} × {qty}")
                with c_sub:
                    st.write(f"₹{item_subtotal:.2f}")

                cart_items_data.append({
                    "name": item["name"],
                    "qty": qty,
                    "price": item["price"],
                    "subtotal": item_subtotal
                })

            # Bill Breakdown
            tax = round(subtotal * 0.05, 2)  # 5% GST
            grand_total = round(subtotal + tax, 2)

            st.markdown("---")
            st.markdown(f"**Subtotal:** ₹{subtotal:.2f}")
            st.markdown(f"**GST (5%):** ₹{tax:.2f}")
            st.markdown(f"### Grand Total: ₹{grand_total:.2f}")

            special_instructions = st.text_input("Special Cooking Instructions (Optional)", placeholder="e.g. Less spicy, extra sauce")

            b_confirm, b_clear = st.columns([2, 1])
            with b_confirm:
                if st.button("✅ Confirm Order", type="primary", use_container_width=True):
                    # Validate Phone if provided
                    clean_phone = customer_phone.strip()
                    if clean_phone and not re.match(r"^(\+?\d{1,4}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?[\d]{7,10}$", clean_phone):
                        st.error("⚠️ Please enter a valid phone number (7-15 digits) or leave it empty.")
                    else:
                        bill_no = database.create_order(
                            table_number=table_number,
                            items=cart_items_data,
                            subtotal=subtotal,
                            tax=tax,
                            total=grand_total,
                            customer_name=customer_name or "Guest",
                            customer_phone=clean_phone,
                            order_type=order_type,
                            notes=special_instructions
                        )
                        st.session_state.cart = {}
                        st.session_state.last_order_bill_no = bill_no
                        st.success(f"🎉 Order Confirmed! Bill No: #{bill_no} for Table {table_number}")
                        st.balloons()
                        st.rerun()

            with b_clear:
                if st.button("Clear", use_container_width=True):
                    clear_cart()
                    st.rerun()

    # If an order was just confirmed, display the receipt summary card
    if st.session_state.last_order_bill_no:
        recent_order = database.get_order_by_bill_no(st.session_state.last_order_bill_no)
        if recent_order:
            st.markdown("---")
            st.markdown(f"""
            <div class="receipt-box">
                <h3 style="color:#0f172a; margin-top:0;">🧾 Order Receipt Summary — Bill #{recent_order['bill_no']}</h3>
                <p><strong>Table:</strong> Table {recent_order['table_number']} &nbsp;|&nbsp; <strong>Guest:</strong> {recent_order['customer_name']} &nbsp;|&nbsp; <strong>Type:</strong> {recent_order['order_type']} &nbsp;|&nbsp; <strong>Time:</strong> {recent_order['time']}</p>
                <p><strong>Status:</strong> <span class="badge-status-placed">{recent_order['status'].upper()}</span></p>
                <hr style="border:none; border-top:1px dashed #cbd5e1; margin:10px 0;">
                <p><strong>Grand Total:</strong> ₹{recent_order['total']:.2f} (Inclusive of GST)</p>
                <p style="color:#64748b; font-size:0.9rem;">Thank you for dining with Aurelius! You can track your kitchen order live in the <strong>🔍 Track Order</strong> tab.</p>
            </div>
            """, unsafe_allow_html=True)


# ==============================================================================
# 2. TRACK ORDER (CUSTOMER LIVE STATUS)
# ==============================================================================
elif nav_choice == "🔍 Track Order":
    st.markdown("<h1 style='text-align:center;'>🔍 Live Order Tracking</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:gray;'>Check the kitchen status of your table's food order in real-time</p>", unsafe_allow_html=True)

    lookup_type = st.radio("Look up order by:", ["Table Number", "Bill / Order Number"], horizontal=True)

    orders_to_display = []
    if lookup_type == "Table Number":
        search_table = st.number_input("Enter Table Number", min_value=1, step=1, value=1)
        if st.button("Search Orders", type="primary"):
            orders_to_display = database.get_orders_by_table(search_table)
    else:
        search_bill = st.number_input("Enter Bill Number", min_value=1, step=1, value=1)
        if st.button("Search Order", type="primary"):
            single_order = database.get_order_by_bill_no(search_bill)
            if single_order:
                orders_to_display = [single_order]

    if orders_to_display:
        st.markdown(f"### Found {len(orders_to_display)} Order(s)")
        for order in orders_to_display:
            status = order.get("status", "Placed")
            status_colors = {
                "Placed": "badge-status-placed",
                "Preparing": "badge-status-preparing",
                "Ready": "badge-status-ready",
                "Served": "badge-status-served",
                "Cancelled": "badge-status-cancelled"
            }
            status_badge_class = status_colors.get(status, "badge-status-placed")

            # Progress bar simulation
            progress_map = {"Placed": 25, "Preparing": 60, "Ready": 90, "Served": 100, "Cancelled": 0}
            progress_val = progress_map.get(status, 25)

            with st.container():
                st.markdown(f"""
                <div class="menu-card">
                    <h4>Bill #{order['bill_no']} — Table {order['table_number']} <span class="{status_badge_class}">{status}</span></h4>
                    <p style="color:#64748b; font-size:0.9rem;"><strong>Time:</strong> {order['time']} | <strong>Guest:</strong> {order.get('customer_name', 'Guest')} | <strong>Total:</strong> ₹{order['total']:.2f}</p>
                </div>
                """, unsafe_allow_html=True)

                if status != "Cancelled":
                    st.progress(progress_val)
                    c_step1, c_step2, c_step3, c_step4 = st.columns(4)
                    c_step1.caption("📝 1. Placed")
                    c_step2.caption("👨‍🍳 2. Preparing")
                    c_step3.caption("🔔 3. Ready")
                    c_step4.caption("✅ 4. Served")

                with st.expander("View Order Items"):
                    for item in order.get("items", []):
                        st.write(f"• {item.get('name', 'Item')} × {item.get('qty', 1)} = ₹{item.get('subtotal', 0):.2f}")
                    if order.get("notes"):
                        st.info(f"Special Instructions: {order['notes']}")
    else:
        st.info("Enter your Table Number or Bill Number above and click Search to view live status.")


# ==============================================================================
# 3. ADMIN PANEL (AUTHENTICATION, ORDERS, CRUD, ANALYTICS)
# ==============================================================================
else:
    st.markdown("<h1 style='text-align:center;'>🧾 Admin Dashboard</h1>", unsafe_allow_html=True)

    # Authentication Gate
    if not st.session_state.admin_authenticated:
        st.markdown("<div style='max-width:400px; margin: 0 auto; padding-top:20px;'>", unsafe_allow_html=True)
        st.subheader("🔐 Staff & Admin Login")

        admin_user_input = st.text_input("Username", value="admin")
        admin_pass_input = st.text_input("Password", type="password")

        if st.button("Log In", type="primary", use_container_width=True):
            if admin_user_input == ADMIN_USER and verify_password(ADMIN_PASSWORD_HASH, admin_pass_input):
                st.session_state.admin_authenticated = True
                st.success("Authentication successful! Welcome to the Admin Panel.")
                st.rerun()
            else:
                st.error("Invalid username or password. Default: admin / admin123")
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        # Authenticated Admin Interface
        top_bar_col1, top_bar_col2 = st.columns([5, 1])
        with top_bar_col1:
            st.caption("Logged in as Administrator (Aurelius Operations)")
        with top_bar_col2:
            if st.button("Logout", use_container_width=True):
                st.session_state.admin_authenticated = False
                st.rerun()

        # Admin Statistics Cards
        stats = database.get_order_statistics()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("💰 Total Revenue", f"₹{stats['total_revenue']:.2f}")
        m2.metric("📦 Total Orders", stats["total_orders"])
        m3.metric("👨‍🍳 Active Kitchen Orders", stats["active_orders"])
        m4.metric("📅 Today's Sales", f"₹{stats['today_revenue']:.2f}")

        st.markdown("---")

        admin_tab1, admin_tab2, admin_tab3 = st.tabs([
            "📋 Order Management",
            "🍽️ Menu Management (CRUD)",
            "📊 Analytics & Reports"
        ])

        # ----------------------------------------------------------------------
        # Admin Tab 1: Live Order Management
        # ----------------------------------------------------------------------
        with admin_tab1:
            st.markdown("### 📋 Restaurant Orders")
            col_filter, col_refresh = st.columns([3, 1])
            with col_filter:
                status_filter = st.selectbox(
                    "Filter Orders by Status",
                    ["All", "Placed", "Preparing", "Ready", "Served", "Cancelled"],
                    index=0
                )
            with col_refresh:
                if st.button("🔄 Refresh Orders", use_container_width=True):
                    st.rerun()

            orders = database.get_all_orders(status_filter=status_filter)

            if not orders:
                st.info("No orders found matching the selected filter.")
            else:
                for order in orders:
                    bill_no = order["bill_no"]
                    table = order["table_number"]
                    time_str = order["time"]
                    total = order["total"]
                    status = order["status"]
                    cust_name = order.get("customer_name", "Guest")
                    cust_phone = order.get("customer_phone", "")

                    with st.expander(f"Bill #{bill_no} | Table {table} | {status.upper()} | ₹{total:.2f} ({time_str})"):
                        c_details, c_actions = st.columns([2, 1.5])

                        with c_details:
                            st.write(f"**Customer:** {cust_name} {f'({cust_phone})' if cust_phone else ''}")
                            st.write(f"**Order Type:** {order.get('order_type', 'Dine-in')}")
                            if order.get("notes"):
                                st.write(f"**Special Notes:** {order['notes']}")
                            st.write("---")
                            st.write("**Ordered Items:**")
                            for item in order.get("items", []):
                                st.write(f"• {item.get('name', 'Item')} × {item.get('qty', 1)} — ₹{item.get('subtotal', 0):.2f}")
                            st.write(f"**Subtotal:** ₹{order.get('subtotal', total):.2f} | **Tax:** ₹{order.get('tax', 0):.2f}")
                            st.markdown(f"#### Total: ₹{total:.2f}")

                        with c_actions:
                            st.write("**Update Order Status:**")
                            if status == "Placed":
                                if st.button(f"👨‍🍳 Start Preparing", key=f"prep_{bill_no}", use_container_width=True):
                                    database.update_order_status(bill_no, "Preparing")
                                    st.rerun()
                            elif status == "Preparing":
                                if st.button(f"🔔 Mark as Ready", key=f"ready_{bill_no}", use_container_width=True):
                                    database.update_order_status(bill_no, "Ready")
                                    st.rerun()
                            elif status == "Ready":
                                if st.button(f"✅ Mark as Served / Paid", key=f"served_{bill_no}", use_container_width=True):
                                    database.update_order_status(bill_no, "Served")
                                    st.rerun()

                            if status not in ["Served", "Cancelled"]:
                                if st.button(f"❌ Cancel Order", key=f"cancel_{bill_no}", use_container_width=True):
                                    database.update_order_status(bill_no, "Cancelled")
                                    st.rerun()

        # ----------------------------------------------------------------------
        # Admin Tab 2: Menu CRUD
        # ----------------------------------------------------------------------
        with admin_tab2:
            st.markdown("### 🍽️ Food Menu Management")

            menu_crud_tabs = st.tabs(["➕ Add New Dish", "✏️ Edit Existing Dishes", "📦 Manage Availability"])

            # Sub-tab: Add New Dish
            with menu_crud_tabs[0]:
                st.subheader("Add a New Dish to Menu")
                with st.form("add_dish_form", clear_on_submit=True):
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        new_name = st.text_input("Dish Name", placeholder="e.g. Crispy Corn")
                        new_category = st.text_input("Category", placeholder="e.g. Starters, Main Course, Desserts")
                        new_price = st.number_input("Price (₹)", min_value=1.0, step=5.0, value=150.0)
                    with col_f2:
                        new_emoji = st.text_input("Emoji Icon", value="🍽️")
                        new_diet = st.radio("Dietary Type", ["Vegetarian", "Non-Vegetarian"])
                        new_desc = st.text_area("Description", placeholder="Ingredients, taste, and serving size...")

                    submitted = st.form_submit_button("➕ Add Dish to Menu", type="primary")
                    if submitted:
                        if not new_name.strip() or not new_category.strip():
                            st.error("Dish Name and Category cannot be empty!")
                        else:
                            database.add_menu_item(
                                name=new_name,
                                category=new_category,
                                price=new_price,
                                emoji=new_emoji,
                                is_veg=1 if new_diet == "Vegetarian" else 0,
                                description=new_desc
                            )
                            st.success(f"Added '{new_name}' to the menu!")
                            st.rerun()

            # Sub-tab: Edit Dishes
            with menu_crud_tabs[1]:
                st.subheader("Edit or Delete Dishes")
                all_items = database.get_all_menu_items()
                if not all_items:
                    st.info("No items in menu.")
                else:
                    selected_item_name = st.selectbox(
                        "Select Dish to Edit",
                        [f"{i['id']}. {i['emoji']} {i['name']} (₹{i['price']})" for i in all_items]
                    )
                    selected_id = int(selected_item_name.split(".")[0])
                    item_to_edit = next(i for i in all_items if i["id"] == selected_id)

                    with st.form(f"edit_form_{selected_id}"):
                        e_c1, e_c2 = st.columns(2)
                        with e_c1:
                            e_name = st.text_input("Dish Name", value=item_to_edit["name"])
                            e_cat = st.text_input("Category", value=item_to_edit["category"])
                            e_price = st.number_input("Price (₹)", value=float(item_to_edit["price"]), min_value=1.0, step=5.0)
                        with e_c2:
                            e_emoji = st.text_input("Emoji", value=item_to_edit["emoji"])
                            e_veg = st.radio("Dietary", ["Vegetarian", "Non-Vegetarian"], index=0 if item_to_edit["is_veg"] == 1 else 1)
                            e_desc = st.text_area("Description", value=item_to_edit.get("description", ""))
                            e_avail = st.checkbox("Available in Stock", value=bool(item_to_edit.get("is_available", 1)))

                        col_update, col_del = st.columns([2, 1])
                        with col_update:
                            update_btn = st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True)
                        with col_del:
                            delete_btn = st.form_submit_button("🗑️ Delete Dish", use_container_width=True)

                        if update_btn:
                            database.update_menu_item(
                                item_id=selected_id,
                                name=e_name,
                                category=e_cat,
                                price=e_price,
                                emoji=e_emoji,
                                is_veg=1 if e_veg == "Vegetarian" else 0,
                                description=e_desc,
                                is_available=1 if e_avail else 0
                            )
                            st.success(f"Updated '{e_name}' successfully!")
                            st.rerun()

                        if delete_btn:
                            database.delete_menu_item(selected_id)
                            st.warning(f"Deleted dish from menu.")
                            st.rerun()

            # Sub-tab: Toggle In Stock / Out of Stock
            with menu_crud_tabs[2]:
                st.subheader("Quick Inventory Availability Toggle")
                all_items = database.get_all_menu_items()
                for item in all_items:
                    col_t1, col_t2 = st.columns([3, 1])
                    with col_t1:
                        st.write(f"{item['emoji']} **{item['name']}** ({item['category']}) - ₹{item['price']}")
                    with col_t2:
                        is_avail = bool(item.get("is_available", 1))
                        btn_label = "✅ In Stock" if is_avail else "❌ Sold Out"
                        if st.button(btn_label, key=f"toggle_{item['id']}", use_container_width=True):
                            database.toggle_item_availability(item["id"])
                            st.rerun()

        # ----------------------------------------------------------------------
        # Admin Tab 3: Analytics & Export
        # ----------------------------------------------------------------------
        with admin_tab3:
            st.markdown("### 📊 Sales Reports & Analytics")
            all_orders_data = database.get_all_orders()

            if not all_orders_data:
                st.info("No order history available for analytics.")
            else:
                # Prepare DataFrame
                df_orders = []
                for o in all_orders_data:
                    df_orders.append({
                        "Bill No": o["bill_no"],
                        "Table": o["table_number"],
                        "Customer": o.get("customer_name", "Guest"),
                        "Order Type": o.get("order_type", "Dine-in"),
                        "Total (₹)": o["total"],
                        "Status": o["status"],
                        "Time": o["time"]
                    })
                df = pd.DataFrame(df_orders)

                st.dataframe(df, use_container_width=True)

                # Export CSV Button
                csv_data = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Export Orders to CSV",
                    data=csv_data,
                    file_name=f"aurelius_orders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )

                st.markdown("#### Orders by Status")
                status_counts = df["Status"].value_counts()
                st.bar_chart(status_counts)
