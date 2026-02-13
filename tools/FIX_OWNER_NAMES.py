import sqlite3
import os

db_path = "data/vault_rodolfo.db"
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
else:
    conn = sqlite3.connect(db_path)
    # Reclamar todos los registros que están en ESTA base de datos para RODOLFO
    # si el servicio o el nombre sugieren que son suyos, o simplemente si están aquí.
    # En un vault local personal, el dueño debería ser el usuario de la cuenta.
    
    # 1. Identificar registros de KIKI que deberían ser de RODOLFO
    cursor = conn.execute("SELECT id, service, username FROM secrets WHERE UPPER(owner_name) = 'KIKI'")
    rows = cursor.fetchall()
    
    if rows:
        print(f">>> Found {len(rows)} records owned by KIKI in RODOLFO's vault. Reclaiming...")
        for row in rows:
            rid, svc, usr = row
            print(f"  Reclaiming record {rid}: {svc} ({usr})")
            conn.execute("UPDATE secrets SET owner_name = 'RODOLFO', synced = 0 WHERE id = ?", (rid,))
        conn.commit()
        print(">>> Reclaiming complete.")
    else:
        print(">>> No mismatched owners found.")
    
    conn.close()
