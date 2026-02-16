import sqlite3
from pathlib import Path

def check_vault_access_schema():
    db_path = "data/vault_rodolfo.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("\n--- Schema of 'vault_access' table ---")
    cursor.execute("PRAGMA table_info(vault_access);")
    for col in cursor.fetchall():
        print(dict(col))

    print("\n--- Vault Access entries ---")
    rows = cursor.execute("SELECT * FROM vault_access;").fetchall()
    for row in rows:
        print(dict(row))

    conn.close()

if __name__ == "__main__":
    check_vault_access_schema()
