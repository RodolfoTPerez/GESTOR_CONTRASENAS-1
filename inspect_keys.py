import sqlite3
db_path = r"c:\PassGuardian_v2\data\vault_rodolfo.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- USERS TABLE ---")
cursor.execute("SELECT username, vault_id, wrapped_vault_key, vault_salt FROM users WHERE username='RODOLFO'")
row = cursor.fetchone()
if row:
    print(f"User: {row[0]}")
    print(f"VaultID: {row[1]}")
    print(f"Key (wrapped): {row[2].hex() if row[2] else 'NONE'}")
    print(f"Salt: {row[3].hex() if row[3] else 'NONE'}")

print("\n--- VAULT_ACCESS TABLE ---")
cursor.execute("SELECT vault_id, wrapped_master_key, access_level FROM vault_access WHERE vault_id='a8e77bff-27da-4bfe-84bf-1efafc07ec71'")
row = cursor.fetchone()
if row:
    print(f"VaultID: {row[0]}")
    print(f"Key (wrapped): {row[1].hex() if row[1] else 'NONE'}")
    print(f"Level: {row[2]}")

conn.close()
