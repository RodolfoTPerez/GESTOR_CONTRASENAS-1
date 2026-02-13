
import sqlite3
import os

db_path = r"c:\PassGuardian_v2\data\vault_rodolfo.db"

if not os.path.exists(db_path):
    print(f"Database NOT found at {db_path}")
    exit(1)

print(f"Opening database: {db_path}")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

print("\n--- ALL SECRETS DUMP ---")
try:
    # Select critical columns to debug key mismatch
    cursor = conn.execute("SELECT id, service, username, is_private, vault_id, owner_name, length(secret) as secret_len, nonce, hex(nonce) as nonce_hex FROM secrets")
    rows = cursor.fetchall()
    print(f"Total rows found: {len(rows)}")
    for row in rows:
        print(dict(row))
except Exception as e:
    print(f"Error querying secrets: {e}")

print("\n--- USER PROFILE DUMP ---")
try:
    cursor = conn.execute("SELECT username, length(password_hash), length(protected_key), vault_id, length(salt), length(vault_salt) FROM users")
    for row in cursor:
        print(dict(row))
except Exception as e:
    print(f"Error querying users: {e}")

conn.close()
