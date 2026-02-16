import sqlite3
import os

dbs = [
    r"c:\PassGuardian_v2\data\vultrax.db",
    r"c:\PassGuardian_v2\src\data\vault_rodolfo.db",
    r"c:\PassGuardian_v2\src\data\passguardian.db"
]

for db_path in dbs:
    if not os.path.exists(db_path):
        print(f"MISSING: {db_path}")
        continue
        
    print(f"\n--- Checking DB: {db_path} ---")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"Tables: {tables}")
        
        if "vault_access" in tables:
            cursor.execute("SELECT vault_id, user_id, wrapped_master_key FROM vault_access")
            rows = cursor.fetchall()
            print(f"Vault Access Rows: {len(rows)}")
            for r in rows:
                v_id = r[0]
                if "a8e7" in str(v_id):
                    print(f"MATCH FOUND: {r}")
        
        if "users" in tables:
            cursor.execute("SELECT username, vault_id, wrapped_vault_key FROM users")
            rows = cursor.fetchall()
            print(f"Users Rows: {len(rows)}")
            for r in rows:
                if "RODOLFO" in str(r[0]).upper():
                    print(f"RODOLFO FOUND: {r}")
                    
    except Exception as e:
        print(f"Error: {e}")
    conn.close()
