import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATABASE_PATH = os.path.join(DATA_DIR, "amazon_app.db")

os.makedirs(DATA_DIR, exist_ok=True)

def get_connection():
    """Return an isolated SQLite connection for the application.

    Keep all database connection behavior in one module so it can be replaced
    later with a MySQL connection manager without changing the app logic.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS amazon_credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                marketplace_id TEXT NOT NULL DEFAULT 'ATVPDKIKX0DER',
                marketplace_name TEXT NOT NULL DEFAULT 'Amazon.com',
                client_id TEXT NOT NULL,
                client_secret TEXT NOT NULL,
                refresh_token TEXT NOT NULL,
                region TEXT NOT NULL DEFAULT 'na',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
        
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS amazon_listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                sku TEXT NOT NULL,
                asin TEXT,
                title TEXT,
                brand TEXT,
                price REAL,
                status TEXT DEFAULT 'draft',
                local_data TEXT,
                amazon_data TEXT,
                last_synced TEXT,
                published_at TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
        
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amazon_order_id TEXT NOT NULL,
                purchase_date TEXT NOT NULL,
                order_status TEXT NOT NULL,
                fulfillment_channel TEXT,
                sales_channel TEXT,
                order_total REAL,
                currency TEXT DEFAULT 'USD',
                shipping_address_city TEXT,
                shipping_address_state TEXT,
                shipping_address_country TEXT,
                shipping_address_postal_code TEXT,
                number_of_items INTEGER DEFAULT 1,
                amazon_fees REAL DEFAULT 0,
                profit REAL DEFAULT 0,
                roi_percent REAL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(amazon_order_id, user_id)
            )
            """
        )
        
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                asin TEXT,
                sku TEXT,
                title TEXT,
                quantity INTEGER DEFAULT 1,
                item_price REAL,
                item_tax REAL,
                shipping_price REAL,
                shipping_tax REAL,
                promotion_discount REAL DEFAULT 0,
                promotion_discount_tax REAL DEFAULT 0,
                FOREIGN KEY (order_id) REFERENCES orders (id)
            )
            """
        )
        
        conn.commit()
