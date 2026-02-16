import sqlite3
import base64

db_path = r"c:\PassGuardian_v2\data\vultrax.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- USERS TABLE ---")
cursor.execute("SELECT username, vault_id, wrapped_vault_key, vault_salt FROM users")
for row in cursor.fetchall():
    print(f"User: {row[0]}, VaultID: {row[1]}, KeyLen: {len(row[2]) if row[2] else 0}, SaltLen: {len(row[3]) if row[3] else 0}")
    if row[0] == "RODOLFO":
        print(f"RODOLFO SALT: {row[3].hex() if row[3] else 'NONE'}")

print("\n--- VAULT_ACCESS TABLE ---")
cursor.execute("SELECT * FROM vault_access")
rows = cursor.fetchall()
print(f"Total rows: {len(rows)}")
for r in rows:
    print(r)

conn.close()
