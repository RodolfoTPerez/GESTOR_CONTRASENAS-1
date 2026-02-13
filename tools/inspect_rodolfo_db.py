
import sqlite3
import os

db_path = r"c:\PassGuardian_v2\data\vault_rodolfo.db"

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

print("--- USER PROFILE ---")
try:
    cursor = conn.execute("SELECT username, role, active, length(password_hash) as pwd_len, length(protected_key) as pkey_len, vault_id FROM users")
    for row in cursor:
        print(dict(row))
except Exception as e:
    print(f"Error querying users: {e}")

print("\n--- LAST 10 SECRETS ---")
try:
    cursor = conn.execute("SELECT id, service, username, is_private, deleted, vault_id, owner_name, length(secret) as secret_len, integrity_hash FROM secrets")
    for row in cursor:
        print(dict(row))
except Exception as e:
    print(f"Error querying secrets: {e}")

conn.close()
