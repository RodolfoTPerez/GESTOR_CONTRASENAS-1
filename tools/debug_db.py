
import sqlite3
import os

db_path = "data/vault_rodolfo.db"
if not os.path.exists(db_path):
    print(f"File {db_path} not found")
else:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT service, username, owner_name, is_private, deleted FROM secrets")
    rows = cursor.fetchall()
    print(f"Found {len(rows)} records in {db_path}:")
    for row in rows:
        print(dict(row))
    conn.close()

db_path_kiki = "data/vault_kiki.db"
if os.path.exists(db_path_kiki):
    conn = sqlite3.connect(db_path_kiki)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT service, username, owner_name, is_private, deleted FROM secrets")
    rows = cursor.fetchall()
    print(f"\nFound {len(rows)} records in {db_path_kiki}:")
    for row in rows:
        print(dict(row))
    conn.close()
