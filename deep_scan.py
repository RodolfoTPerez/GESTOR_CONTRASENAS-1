import sqlite3
dbs = [
    r"c:\PassGuardian_v2\vault_rodolfo.db",
    r"c:\PassGuardian_v2\data\vault_rodolfo.db",
    r"c:\PassGuardian_v2\src\data\vault_rodolfo.db"
]

for db in dbs:
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"\nDB: {db}")
        print(f"Tables: {tables}")
        if "users" in tables:
            cursor.execute("SELECT username FROM users")
            print(f"Users: {cursor.fetchall()}")
        if "vault_access" in tables:
            cursor.execute("SELECT vault_id FROM vault_access")
            print(f"VaultIDs: {cursor.fetchall()}")
        conn.close()
    except Exception as e:
        print(f"Failed {db}: {e}")
