import sqlite3
from pathlib import Path

def get_dani_id():
    conn = sqlite3.connect("data/vault_dani.db")
    user = conn.execute("SELECT user_id, username FROM users WHERE username='DANI'").fetchone()
    print(f"DANI mapping: {dict(user)}")
    conn.close()

if __name__ == "__main__":
    get_dani_id()
