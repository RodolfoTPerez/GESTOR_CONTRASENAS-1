import sqlite3
from pathlib import Path

def dump_all_vault_access():
    data_dir = Path("data")
    for db_path in data_dir.glob("*.db"):
        print(f"\n--- Vault Access in {db_path.name} ---")
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vault_access'")
            if not cursor.fetchone():
                print("Table 'vault_access' not found.")
                continue
                
            rows = cursor.execute("SELECT * FROM vault_access").fetchall()
            for row in rows:
                d = dict(row)
                # Filter blob for display
                if 'wrapped_master_key' in d and d['wrapped_master_key']:
                    d['wrapped_master_key'] = d['wrapped_master_key'].hex()[:20] + "..."
                print(d)
                
            # Also check users table for wrapped_vault_key
            print(f"--- Users table in {db_path.name} ---")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            if cursor.fetchone():
                users = cursor.execute("SELECT username, wrapped_vault_key, vault_salt FROM users").fetchall()
                for u in users:
                    ud = dict(u)
                    if ud['wrapped_vault_key']: ud['wrapped_vault_key'] = ud['wrapped_vault_key'].hex()[:20] + "..."
                    if ud['vault_salt']: ud['vault_salt'] = ud['vault_salt'].hex()[:20] + "..."
                    print(ud)
            
            conn.close()
        except Exception as e:
            print(f"Error reading {db_path.name}: {e}")

if __name__ == "__main__":
    dump_all_vault_access()
