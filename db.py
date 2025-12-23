import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path("data.sqlite3")

def conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db() -> None:
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS products (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          sku TEXT UNIQUE,
          title TEXT NOT NULL,
          price_rub INTEGER NOT NULL,
          in_stock INTEGER NOT NULL DEFAULT 1,
          lot_url TEXT,
          note TEXT
        );

        CREATE TABLE IF NOT EXISTS leads (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          tg_user_id INTEGER,
          tg_username TEXT,
          name TEXT,
          contact TEXT,
          message TEXT,
          created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS orders (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          tg_user_id INTEGER,
          tg_username TEXT,
          product_id INTEGER,
          qty INTEGER,
          grind TEXT,
          delivery_city TEXT,
          comment TEXT,
          created_at TEXT DEFAULT (datetime('now')),
          FOREIGN KEY(product_id) REFERENCES products(id)
        );
        """)

def seed_demo_products() -> None:
    demo = [
        ("LOT-UG-001", "Uganda — Natural — 250g", 950, 1, None, "ягоды, какао, ром"),
        ("LOT-CO-014", "Colombia — Washed — 1kg", 3200, 1, None, "цитрус, карамель"),
        ("LOT-ET-007", "Ethiopia — Honey — 250g", 1100, 1, None, "жасмин, персик"),
    ]
    with conn() as c:
        for sku, title, price, stock, url, note in demo:
            c.execute("""
              INSERT OR IGNORE INTO products(sku,title,price_rub,in_stock,lot_url,note)
              VALUES(?,?,?,?,?,?)
            """, (sku, title, price, stock, url, note))

def list_products(offset: int = 0, limit: int = 6) -> list[sqlite3.Row]:
    with conn() as c:
        return c.execute("""
          SELECT * FROM products WHERE in_stock=1 ORDER BY id DESC LIMIT ? OFFSET ?
        """, (limit, offset)).fetchall()

def get_product(product_id: int) -> sqlite3.Row | None:
    with conn() as c:
        return c.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()

def create_lead(user_id: int, username: str | None, name: str, contact: str, message: str) -> int:
    with conn() as c:
        cur = c.execute("""
          INSERT INTO leads(tg_user_id,tg_username,name,contact,message)
          VALUES(?,?,?,?,?)
        """, (user_id, username, name, contact, message))
        return int(cur.lastrowid)

def create_order(user_id: int, username: str | None, product_id: int, qty: int, grind: str, city: str, comment: str) -> int:
    with conn() as c:
        cur = c.execute("""
          INSERT INTO orders(tg_user_id,tg_username,product_id,qty,grind,delivery_city,comment)
          VALUES(?,?,?,?,?,?,?)
        """, (user_id, username, product_id, qty, grind, city, comment))
        return int(cur.lastrowid)
