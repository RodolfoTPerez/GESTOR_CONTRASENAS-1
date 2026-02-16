import sqlite3
db_path = r"c:\PassGuardian_v2\data\vultrax.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT username, vault_id, wrapped_vault_key FROM users")
rows = cursor.fetchall()
print(f"Users found: {len(rows)}")
for r in rows:
    print(r)
conn.close()
