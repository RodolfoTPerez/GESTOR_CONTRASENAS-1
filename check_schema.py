import sqlite3
db_path = r"c:\PassGuardian_v2\data\vultrax.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(vault_access)")
print(f"vault_access columns: {cursor.fetchall()}")
cursor.execute("SELECT * FROM vault_access LIMIT 5")
print(f"vault_access contents: {cursor.fetchall()}")
conn.close()
