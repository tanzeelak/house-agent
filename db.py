import sqlite3
import json
from datetime import datetime

DB_PATH = "house_agent.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS roommates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE NOT NULL,
            name TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roommate_phone TEXT NOT NULL,
            body TEXT NOT NULL,
            direction TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roommate_phone TEXT NOT NULL,
            intent TEXT NOT NULL,
            confidence REAL NOT NULL,
            is_urgent REAL NOT NULL,
            raw_message TEXT NOT NULL,
            extracted_details TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def upsert_roommate(phone: str, name: str = None):
    conn = get_db()
    conn.execute(
        "INSERT INTO roommates (phone, name, created_at) VALUES (?, ?, ?) ON CONFLICT(phone) DO UPDATE SET name = COALESCE(?, name)",
        (phone, name, datetime.utcnow().isoformat(), name),
    )
    conn.commit()
    conn.close()


def save_message(phone: str, body: str, direction: str = "inbound"):
    conn = get_db()
    conn.execute(
        "INSERT INTO messages (roommate_phone, body, direction, created_at) VALUES (?, ?, ?, ?)",
        (phone, body, direction, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def save_request(phone: str, intent: str, confidence: float, is_urgent: float, raw_message: str, extracted_details: dict = None):
    conn = get_db()
    conn.execute(
        "INSERT INTO requests (roommate_phone, intent, confidence, is_urgent, raw_message, extracted_details, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (phone, intent, confidence, is_urgent, raw_message, json.dumps(extracted_details) if extracted_details else None, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def get_pending_requests():
    conn = get_db()
    rows = conn.execute("SELECT * FROM requests WHERE status = 'pending' ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# Initialize on import
init_db()
