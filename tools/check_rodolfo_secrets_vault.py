import sqlite3
import os

db_path = "data/vault_rodolfo.db"
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
else:
    conn = sqlite3.connect(db_path)
    # Check if vault_id column exists
    cursor = conn.execute("PRAGMA table_info(secrets)")
    cols = [c[1] for c in cursor.fetchall()]
    
    query = "SELECT id, service, is_private, owner_name, vault_id FROM secrets"
    cursor = conn.execute(query)
    rows = cursor.fetchall()
    print("ID | Service | Private | Owner | Vault ID")
    print("-" * 80)
    for row in rows:
        print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}")
    conn.close()
