import sqlite3
from pathlib import Path

def compare_secrets():
    dbs = ["data/vault_rodolfo.db", "data/vault_dani.db"]
    for db_path in dbs:
        if not Path(db_path).exists():
            print(f"Database {db_path} not found.")
            continue

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        print(f"\n--- Secrets in {db_path} ---")
        query = "SELECT count(*) FROM secrets WHERE owner_name LIKE '%DANI%' OR username LIKE '%DANI%';"
        count = cursor.execute(query).fetchone()[0]
        print(f"Total DANI secrets: {count}")
        
        rows = cursor.execute("SELECT id, service, vault_id FROM secrets WHERE owner_name LIKE '%DANI%' OR username LIKE '%DANI%' LIMIT 5;").fetchall()
        for row in rows:
            print(dict(row))

        conn.close()

if __name__ == "__main__":
    compare_secrets()
