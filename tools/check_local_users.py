from pathlib import Path
import os
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
import sqlite3
from pathlib import Path

db_path = Path(str(BASE_DIR) + "/data/passguardian.db")

if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    
    print(f"Usuarios en passguardian.db: {count}")
    
    if count > 0:
        cursor.execute("SELECT username FROM users")
        users = cursor.fetchall()
        print(f"Usuarios: {users}")
    
    conn.close()
else:
    print("passguardian.db NO EXISTE")

# Verificar vault_rodolfo.db
vault_db = Path(str(BASE_DIR) + "/data/vault_rodolfo.db")
if vault_db.exists():
    conn = sqlite3.connect(str(vault_db))
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    
    print(f"\nUsuarios en vault_rodolfo.db: {count}")
    
    if count > 0:
        cursor.execute("SELECT username FROM users")
        users = cursor.fetchall()
        print(f"Usuarios: {users}")
    
    conn.close()
else:
    print("\nvault_rodolfo.db NO EXISTE")
