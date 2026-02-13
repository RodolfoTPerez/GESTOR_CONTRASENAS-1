
import sqlite3
import os

db_path = "data/passguardian.db"
if not os.path.exists(db_path):
    print(f"File {db_path} not found")
else:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT username, role, vault_id, user_id FROM users")
    rows = cursor.fetchall()
    print(f"Found {len(rows)} users in {db_path}:")
    for row in rows:
        print(dict(row))
    conn.close()
