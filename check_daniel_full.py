import sqlite3
from pathlib import Path

USERNAME = "RODOLFO"
DB_FILE = Path(f"data/vault_{USERNAME.lower()}.db")

def check_daniel_records():
    if not DB_FILE.exists():
        print(f"Database {DB_FILE} not found.")
        return

    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("\n--- All Secrets for DANIEL ---")
    query = "SELECT id, service, username, owner_name, vault_id FROM secrets WHERE owner_name LIKE '%DANIEL%' OR username LIKE '%DANIEL%';"
    rows = cursor.execute(query).fetchall()
    for row in rows:
        print(dict(row))

    print("\n--- All Vault Accesses ---")
    rows = cursor.execute("SELECT vault_id, access_level, synced FROM vault_access;").fetchall()
    for row in rows:
        print(dict(row))

    conn.close()

if __name__ == "__main__":
    check_daniel_records()
