import sqlite3
import os

db_path = "data/vault_rodolfo.db"
conn = sqlite3.connect(db_path)
cursor = conn.execute("SELECT username, salt, vault_salt, password_hash FROM users WHERE username = 'RODOLFO'")
row = cursor.fetchone()
if row:
    print(f"Username: {row[0]}")
    print(f"Login Salt: {row[1]}")
    print(f"Vault Salt (hex): {row[2].hex() if row[2] else 'None'}")
    print(f"Pass Hash: {row[3]}")
conn.close()
