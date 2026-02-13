import sqlite3
import os

db_path = r'c:\PassGuardian_v2\data\vault_rodolfo.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT owner_name, username, service FROM secrets WHERE owner_name != username AND is_private = 0")
    rows = cursor.fetchall()
    print(f"Encontrados {len(rows)} registros con discrepancia de nombre:")
    for r in rows:
        print(f"Owner: {r[0]}, Username: {r[1]}, Service: {r[2]}")
    conn.close()
else:
    print("Base de datos no encontrada.")
