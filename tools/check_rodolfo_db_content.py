import sqlite3
import os

db_path = "data/vault_rodolfo.db"
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT id, service, username, is_private, owner_name, deleted FROM secrets")
    rows = cursor.fetchall()
    print("ID | Service | Username | Private | Owner | Deleted")
    print("-" * 60)
    for row in rows:
        print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}")
    conn.close()
