import sqlite3
from pathlib import Path

def check_dani_db():
    db_path = "data/vault_dani.db"
    if not Path(db_path).exists():
        print(f"Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print(f"\n--- vault_access in {db_path} ---")
    rows = cursor.execute("SELECT * FROM vault_access;").fetchall()
    for row in rows:
        print(dict(row))

    print(f"\n--- users in {db_path} ---")
    rows = cursor.execute("SELECT username, vault_id, wrapped_vault_key, vault_salt FROM users;").fetchall()
    for row in rows:
        print(dict(row))

    conn.close()

if __name__ == "__main__":
    check_dani_db()
