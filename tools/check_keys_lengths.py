import sqlite3
import os

db_path = "data/vault_rodolfo.db"
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT username, protected_key, wrapped_vault_key FROM users")
    rows = cursor.fetchall()
    print("Username | Protected Key (length) | Wrapped Vault Key (length)")
    print("-" * 80)
    for row in rows:
        pk_len = len(row[1]) if row[1] else 0
        wvk_len = len(row[2]) if row[2] else 0
        print(f"{row[0]} | {pk_len} | {wvk_len}")
    conn.close()
