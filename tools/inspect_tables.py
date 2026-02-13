
import sqlite3
import os

db_path = r'c:\PassGuardian_v2\data\vault_rodolfo.db'
if not os.path.exists(db_path):
    print(f"File not found: {db_path}")
    exit()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def print_table(name):
    print(f"\n--- TABLE: {name} ---")
    cursor.execute(f"PRAGMA table_info({name});")
    info = cursor.fetchall()
    print("Columns:", [col[1] for col in info])
    
    cursor.execute(f"SELECT * FROM {name} LIMIT 3;")
    rows = cursor.fetchall()
    for row in rows:
        # Mask sensitive data if any
        masked_row = list(row)
        # For 'users' table, we might want to mask password_hash
        if name == 'users':
            # Column indices: id, username, password_hash, salt, totp_secret, role, active, created_at, ...
            # Let's just find where password_hash and totp_secret are
            for i, col in enumerate(info):
                if col[1] in ['password_hash', 'totp_secret', 'salt', 'vault_salt']:
                    if masked_row[i]:
                        masked_row[i] = "[MASKED]"
        print(masked_row)

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall() if t[0] != 'sqlite_sequence']

for table in tables:
    print_table(table)

conn.close()
