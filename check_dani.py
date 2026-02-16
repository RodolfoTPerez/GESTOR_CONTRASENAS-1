import sqlite3
from pathlib import Path

def check_dani_records(db_path):
    if not Path(db_path).exists():
        print(f"Database {db_path} not found.")
        return

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print(f"\n--- Searching in {db_path} ---")
    query = "SELECT id, service, username, owner_name, vault_id FROM secrets WHERE owner_name LIKE '%DANI%' OR username LIKE '%DANI%';"
    rows = cursor.execute(query).fetchall()
    if not rows:
        print("No records found with DANI.")
    for row in rows:
        print(dict(row))

    conn.close()

if __name__ == "__main__":
    check_dani_records("data/vault_rodolfo.db")
    check_dani_records("data/vultrax.db")
