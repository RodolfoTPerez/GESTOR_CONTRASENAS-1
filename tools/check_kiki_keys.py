import sqlite3
import base64

# Check KIKI's vault keys
conn = sqlite3.connect(r'C:\PassGuardian_v2\data\vault_kiki.db')

print("=== KIKI's User Profile ===")
cursor = conn.execute("""
    SELECT username, vault_id, vault_salt, protected_key, wrapped_vault_key, user_id
    FROM users 
    WHERE username = 'KIKI'
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
    print("KIKI not found")

print("\n=== Vault Access Table ===")
cursor = conn.execute("SELECT vault_id, wrapped_master_key FROM vault_access")
for row in cursor:
    print(f"Vault ID: {row[0]}")
    print(f"Wrapped Master Key: {len(row[1]) if row[1] else 0} bytes")

print("\n=== Sample Secret ===")
cursor = conn.execute("SELECT service, owner_name, key_type FROM secrets LIMIT 1")
row = cursor.fetchone()
if row:
    print(f"Service: {row[0]}")
    print(f"Owner: {row[1]}")
    print(f"Key Type: {row[2]}")

conn.close()
