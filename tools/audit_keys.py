
import sqlite3
import os
from pathlib import Path

def audit_kiki_records():
    db_path = Path("data/vault_rodolfo.db")
    if not db_path.exists():
        print(f"Error: Base de datos no encontrada en {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Ver registros de KIKI que son publicos
    cur.execute("SELECT id, service, owner_name, is_private FROM secrets WHERE owner_name = 'KIKI'")
    rows = cur.fetchall()
    
    print(f"\nAUDITORÍA DE REGISTROS DE 'KIKI' EN LA BÓVEDA DE RODOLFO:")
    print("-" * 60)
    if not rows:
        print("No se encontraron registros creados por KIKI.")
    else:
        for r in rows:
            print(f"ID: {r[0]} | Servicio: {r[1]} | Dueño: {r[2]} | Privado: {r[3]}")
    
    conn.close()

if __name__ == "__main__":
    audit_kiki_records()
