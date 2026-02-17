import sqlite3

# Check RODOLFO's vault keys
conn = sqlite3.connect(r'C:\PassGuardian_v2\data\vault_rodolfo.db')

print("=== RODOLFO's User Profile ===")
cursor = conn.execute("""
    SELECT username, vault_id, vault_salt, protected_key, wrapped_vault_key, user_id
    FROM users 
    WHERE username = 'RODOLFO'
""")
row = cursor.fetchone()
if row:
    print(f"Username: {row[0]}")
    print(f"Vault ID: {row[1]}")
    print(f"Vault Salt: {len(row[2]) if row[2] else 0} bytes")
    print(f"Protected Key (SVK): {len(row[3]) if row[3] else 0} bytes")
    print(f"Wrapped Vault Key: {len(row[4]) if row[4] else 0} bytes")
    print(f"User ID: {row[5]}")
else:
    print("RODOLFO not found")

print("\n=== Vault Access Table ===")
cursor = conn.execute("SELECT vault_id, wrapped_master_key FROM vault_access")
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(f"Vault ID: {row[0]}")
        print(f"Wrapped Master Key: {len(row[1]) if row[1] else 0} bytes")
else:
    print("No vault_access entries")

conn.close()
