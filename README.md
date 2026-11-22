# Aurelius — Restaurant Food Ordering System

A full-stack restaurant food ordering and kitchen management platform developed with Python, Streamlit, and SQLite. Aurelius provides an interactive table-ordering web application for diners, real-time kitchen tracking, administrative order management, dynamic menu controls, and a synchronized terminal CLI interface.

---

## Key Highlights

- **Customer Ordering:** Interactive digital menu with category filtering, real-time keyword search, vegetarian/non-vegetarian toggles, item descriptions, and cart management.
- **Table & Dining Options:** Supports Dine-in and Takeaway workflows with table numbering, guest details, and kitchen notes.
- **Order Tracking:** Live customer order lookup by table number or bill token showing stage-by-stage kitchen progress (`Placed` ➔ `Preparing` ➔ `Ready` ➔ `Served`).
- **Admin Dashboard:** Password-protected management console with revenue analytics, live order status progression, menu CRUD operations, and stock inventory toggles.
- **Data Persistence:** Relational SQLite database (`restaurant.db`) with automatic table initialization, schema seeding, and atomic dual-write synchronization to `bills.json`.
- **Synchronized CLI:** Terminal interface (`food.py`) sharing dynamic menu items and order records with the web application.

---

## Project Structure

```
Food_ordering_system/
├── app.py              # Primary Streamlit web application
├── database.py         # SQLite data access layer and synchronization helpers
├── food.py             # Alternative terminal console ordering interface
├── bills.json          # Synchronized JSON order persistence file
├── requirements.txt    # Project dependencies
├── .gitignore          # Git exclusion rules
└── README.md           # Project documentation
```

---

## Installation & Setup

### 1. Prerequisites
- Python 3.10 or higher installed on your machine.
- Git installed.

### 2. Clone the Repository
```bash
git clone https://github.com/<your-username>/Food_ordering_system.git
cd Food_ordering_system
```

### 3. Create and Activate a Virtual Environment
- **On Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
- **On macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Running the Application

### Launch the Web Application
```bash
python -m streamlit run app.py
```
Once started, open your web browser at:
`http://localhost:8501`

### Launch the Terminal CLI
```bash
python food.py
```

---

## Default Staff Credentials

Access to the Admin Dashboard (`🧾 Admin Panel` in the sidebar) requires authentication:
- **Default Username:** `admin`
- **Default Password:** `admin123`

*Note: Passwords are cryptographically verified using salted PBKDF2-HMAC-SHA256 with 100,000 iterations.*

---

## Database Architecture

Aurelius automatically initializes its SQLite database (`restaurant.db`) upon first launch.

- `menu_items`: Stores dish titles, categories, pricing, emoji icons, dietary tags, descriptions, and stock status.
- `orders`: Stores unique bill numbers, customer details, table assignments, itemized JSON, subtotal, tax breakdown, live order status, and timestamps.
- `bills.json`: Automatically synchronized via atomic file replacement to preserve backward compatibility for scripts and CLI utilities.
