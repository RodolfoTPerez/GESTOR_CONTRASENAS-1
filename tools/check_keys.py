import sqlite3
import os

db_path = r"c:\PassGuardian_v2\data\vault_kiki.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT username, vault_id, length(vault_salt), length(protected_key), length(wrapped_vault_key) FROM users")
    rows = cursor.fetchall()
    print(f"--- Diagnóstico de Seguridad: KIKI ---")
    for row in rows:
        print(f"Usuario: {row[0]}")
        print(f"Vault ID: {row[1]}")
        print(f"Salt Size: {row[2]} bytes")
        print(f"Protected (SVK) Size: {row[3]} bytes")
        print(f"Wrapped (Vault) Size: {row[4]} bytes")
    conn.close()
else:
    print("Database not found")
