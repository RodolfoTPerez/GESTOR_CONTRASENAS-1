import sqlite3
from pathlib import Path

def check_dani_details():
    db_path = "data/vault_rodolfo.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print(f"\n--- Details for DANI records ---")
    query = "SELECT id, service, is_private, vault_id, key_type FROM secrets WHERE owner_name LIKE '%DANI%' OR username LIKE '%DANI%';"
    rows = cursor.execute(query).fetchall()
    for row in rows:
        print(dict(row))

    conn.close()

if __name__ == "__main__":
    check_dani_details()
