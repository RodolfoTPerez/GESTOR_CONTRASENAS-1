
import sqlite3
import os
import sys

# Ensure UTF-8 output if possible
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def emergency_purge_leaked_secrets():
    """
    Elimina registros privados de otros usuarios que se hayan filtrado
    a la base de datos local debido a una política de sincronización débil.
    """
    # 1. Identificar bóvedas locales
    data_dir = "data"
    if not os.path.exists(data_dir):
        print(f"Directory {data_dir} not found.")
        return

    dbs = [f for f in os.listdir(data_dir) if f.startswith("vault_") and f.endswith(".db")]
    
    for db_name in dbs:
        db_path = os.path.join(data_dir, db_name)
        username = db_name.replace("vault_", "").replace(".db", "").upper()
        
        print(f">>> Investigando {db_path} (Propietario esperado: {username})")
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            
            # Buscar registros privados que NO pertenecen al dueño de la bóveda
            leaked = conn.execute(
                "SELECT id, service, owner_name FROM secrets WHERE is_private = 1 AND UPPER(owner_name) != ?",
                (username,)
            ).fetchall()
            
            if leaked:
                print(f"    [ALERTA] ENCONTRADOS {len(leaked)} REGISTROS FILTRADOS!")
                for r in leaked:
                    print(f"    - Servicio: {r['service']} | Dueno Real: {r['owner_name']}")
                
                # PURGAR
                count = conn.execute(
                    "DELETE FROM secrets WHERE is_private = 1 AND UPPER(owner_name) != ?",
                    (username,)
                ).rowcount
                conn.commit()
                print(f"    [OK] PURGADOS {count} registros con éxito.")
            else:
                print("    [SAFE] No se encontraron registros privados filtrados.")
            
            conn.close()
        except Exception as e:
            print(f"    [ERROR] Error procesando {db_name}: {e}")

if __name__ == "__main__":
    emergency_purge_leaked_secrets()
