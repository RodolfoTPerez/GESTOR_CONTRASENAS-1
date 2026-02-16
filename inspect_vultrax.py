import sqlite3
from pathlib import Path

def check_vultrax():
    db_path = "data/vultrax.db"
    if not Path(db_path).exists():
        print(f"Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print(f"\n--- users in {db_path} ---")
    try:
        rows = cursor.execute("SELECT username, vault_id, wrapped_vault_key, vault_salt FROM users WHERE username='RODOLFO';").fetchall()
        for row in rows:
            print(dict(row))
    except:
        print("Table 'users' not in vultrax.db or different schema.")

    print(f"\n--- Tables in vultrax.db ---")
    rows = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    for row in rows:
        print(dict(row))

    conn.close()

if __name__ == "__main__":
    check_vultrax()
