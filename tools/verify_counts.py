import sqlite3
import os

data_dir = r"c:\PassGuardian_v2\data"
dbs = ["vault_kiki.db", "vault_karen.db", "vault_daniel.db", "vault_rodolfo.db"]

for db in dbs:
    path = os.path.join(data_dir, db)
    if os.path.exists(path):
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM secrets WHERE deleted=0")
        count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM secrets WHERE is_private=1 AND deleted=0")
        priv = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM secrets WHERE is_private=0 AND deleted=0")
        pub = cursor.fetchone()[0]
        print(f"{db}: Total={count}, Privados={priv}, Publicos={pub}")
        conn.close()
    else:
        print(f"{db} not found")
