import sqlite3
from pathlib import Path

def get_dani_id():
    conn = sqlite3.connect("data/vault_dani.db")
    user = conn.execute("SELECT user_id, username FROM users WHERE username='DANI'").fetchone()
    if user:
        print(f"DANI Username: {user[1]}")
        print(f"DANI UUID:     {user[0]}")
    else:
        print("DANI not found.")
    conn.close()

if __name__ == "__main__":
    get_dani_id()
