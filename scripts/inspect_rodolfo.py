
import sqlite3
import os

db_path = "data/vault_rodolfo.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    print("--- Database: users ---")
    rows = conn.execute("SELECT username, vault_id, wrapped_vault_key, vault_salt FROM users WHERE UPPER(username) = 'RODOLFO'").fetchall()
    for r in rows:
        print(f"User: {r['username']}")
        print(f"Vault ID: {r['vault_id']}")
        print(f"Wrapped Key (len): {len(r['wrapped_vault_key']) if r['wrapped_vault_key'] else 'None'}")
        print(f"Vault Salt (hex): {r['vault_salt'].hex() if r['vault_salt'] else 'None'}")
    
    print("\n--- Database: vault_access ---")
    rows = conn.execute("SELECT * FROM vault_access").fetchall()
    for r in rows:
        print(f"Vault ID: {r['vault_id']}")
        print(f"Access Level: {r['access_level']}")
        print(f"Wrapped Key (len): {len(r['wrapped_master_key']) if r['wrapped_master_key'] else 'None'}")
    
    conn.close()
else:
    print(f"Database {db_path} not found.")
