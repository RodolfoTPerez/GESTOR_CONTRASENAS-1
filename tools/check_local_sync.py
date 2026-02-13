from pathlib import Path
import os
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
import sqlite3
import os
from pathlib import Path

def check_local_secrets():
    data_dir = Path(str(BASE_DIR) + "/data")
    db_path = data_dir / "vault_rodolfo.db"
    
    if not db_path.exists():
        print(f"La base de datos {db_path} no existe.")
        return

    print(f"Conectando a {db_path}...")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT service, username, is_private, synced, cloud_id FROM secrets")
        rows = cursor.fetchall()
        
        print(f"\nREGISTROS EN vault_rodolfo.db ({len(rows)} encontrados):")
        print("-" * 80)
        print(f"{'SERVICIO':20} | {'USUARIO':15} | {'PRIVADO?':8} | {'SYNC?':6} | {'CLOUD_ID'}")
        print("-" * 80)
        
        for r in rows:
            priv = "SI" if r[2] == 1 else "NO"
            sync = "OK" if r[3] == 1 else "PEND"
            cid = r[4] if r[4] else "None"
            print(f"{r[0]:20} | {r[1]:15} | {priv:8} | {sync:6} | {cid}")
            
    except Exception as e:
        print(f"Error consultando la tabla: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_local_secrets()
