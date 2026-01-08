import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "passguardian.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Creación de tablas básicas (sin datos sensibles por ahora)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS master (
        id INTEGER PRIMARY KEY,
        created_at TIMESTAMP,
        verifier TEXT,
        nonce TEXT,
        failed INTEGER,
        locked_until REAL,
        salt TEXT,
        email TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS totp (
        id INTEGER PRIMARY KEY,
        created_at TIMESTAMP,
        secret TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        created_at TIMESTAMP,
        username TEXT,
        role TEXT,
        active BOOLEAN
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        session_token TEXT,
        user_id TEXT,
        ip_address TEXT,
        device_info TEXT,
        created_at TIMESTAMP,
        last_activity TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS secrets (
        id TEXT PRIMARY KEY,
        created_at TIMESTAMP,
        service TEXT,
        user TEXT,
        secret BLOB,
        nonce BLOB
    );
    """)

    conn.commit()
    conn.close()
