import sqlite3
import os

db_path = "data/vault_rodolfo.db"
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT username, vault_id, role FROM users")
    rows = cursor.fetchall()
    print("Username | Vault ID | Role")
    print("-" * 60)
    for row in rows:
        print(f"{row[0]} | {row[1]} | {row[2]}")
    conn.close()
