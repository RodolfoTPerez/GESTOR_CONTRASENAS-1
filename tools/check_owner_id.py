import sqlite3
import os

db_path = "data/vault_rodolfo.db"
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT id, service, username, is_private, owner_name, owner_id FROM secrets WHERE id IN (108, 109)")
    rows = cursor.fetchall()
    print("ID | Service | Username | Private | Owner Name | Owner ID")
    print("-" * 80)
    for row in rows:
        print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}")
    conn.close()
