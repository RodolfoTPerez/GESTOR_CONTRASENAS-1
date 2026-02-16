import sqlite3
db_path = r"c:\PassGuardian_v2\data\vault_rodolfo.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM secrets WHERE vault_id='a8e77bff-27da-4bfe-84bf-1efafc07ec71'")
print(f"Secrets in vault a8e7...: {cursor.fetchone()[0]}")
cursor.execute("SELECT service, username FROM secrets LIMIT 10")
for r in cursor.fetchall():
    print(r)
conn.close()
