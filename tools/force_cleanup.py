
import sqlite3
import os
from pathlib import Path

def clean_kik1():
    db_path = Path("data/vault_rodolfo.db")
    if not db_path.exists():
        print("Bóveda local no encontrada.")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # 1. Verificar si existe localmente
    cur.execute("SELECT id, service, owner_name FROM secrets WHERE service = 'KIK1'")
    row = cur.fetchone()
    
    if row:
        print(f"Encontrado localmente: ID {row[0]}, Servicio {row[1]}, Dueño {row[2]}")
        # 2. Borrarlo físicamente de la DB local
        cur.execute("DELETE FROM secrets WHERE service = 'KIK1'")
        conn.commit()
        print("Registro KIK1 eliminado físicamente de la base de datos local.")
    else:
        print("KIK1 no encontrado en la base de datos local.")
    
    conn.close()

if __name__ == "__main__":
    clean_kik1()
