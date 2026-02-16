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

    print("\n--- Schema of 'secrets' table ---")
    cursor.execute("PRAGMA table_info(secrets);")
    for col in cursor.fetchall():
        print(dict(col))

    print("\n--- Secrets count ---")
    cursor.execute("SELECT count(*) FROM secrets;")
    print(f"Total secrets: {cursor.fetchone()[0]}")

    print("\n--- Secrets samples ---")
    rows = cursor.execute("SELECT * FROM secrets LIMIT 5;").fetchall()
    for row in rows:
        print(dict(row))

    print("\n--- Vault Access for RODOLFO ---")
    query = "SELECT * FROM vault_access;"
    rows = cursor.execute(query).fetchall()
    for row in rows:
        print(dict(row))

    conn.close()

if __name__ == "__main__":
    check_daniel_records()
