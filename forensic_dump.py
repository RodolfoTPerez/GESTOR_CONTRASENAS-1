import sqlite3
import os

db_path = r"c:\PassGuardian_v2\data\vault_rodolfo.db"

def dump_stats():
    if not os.path.exists(db_path):
        print(f"DB not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("--- USERS TABLE ---")
    try:
        cursor.execute("SELECT username, vault_id, length(protected_key) as pk_len, length(wrapped_vault_key) as wvk_len, hex(vault_salt) as salt_hex FROM users")
        for row in cursor.fetchall():
            print(f"User: {row['username']} | VaultID: {row['vault_id']} | PK_Len: {row['pk_len']} | WVK_Len: {row['wvk_len']} | Salt: {row['salt_hex']}")
    except Exception as e:
        print(f"Error reading users: {e}")

    print("\n--- VAULT_ACCESS TABLE ---")
    try:
        cursor.execute("SELECT vault_id, length(wrapped_master_key) as wmk_len, synced, updated_at FROM vault_access")
        for row in cursor.fetchall():
            print(f"VaultID: {row['vault_id']} | WMK_Len: {row['wmk_len']} | Synced: {row['synced']} | Updated: {row['updated_at']}")
    except Exception as e:
        print(f"Error reading vault_access: {e}")

    print("\n--- META TABLE ---")
    try:
        cursor.execute("SELECT key, hex(value) as val_hex FROM meta")
        for row in cursor.fetchall():
            print(f"Key: {row['key']} | Value: {row['val_hex']}")
    except Exception as e:
        print(f"Error reading meta: {e}")

    conn.close()

if __name__ == "__main__":
    dump_stats()
