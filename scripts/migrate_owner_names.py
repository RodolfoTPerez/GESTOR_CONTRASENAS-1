"""
Script de Migración: Asignar owner_name a servicios existentes
===============================================================
Este script actualiza todos los servicios que tienen owner_name = NULL
para que pertenezcan al usuario actual de la bóveda.
"""

import sqlite3
from pathlib import Path

def migrate_owner_names():
    """Migra todos los servicios sin owner_name."""
    
    data_dir = Path("data")
    vault_files = list(data_dir.glob("vault_*.db"))
    
    print("=" * 70)
    print("MIGRACIÓN: Asignando owner_name a servicios sin dueño")
    print("=" * 70)
    
    for vault_file in vault_files:
        # Extraer el nombre del usuario desde el nombre del archivo
        username = vault_file.stem.replace("vault_", "").upper()
        
        print(f"\n[DB: {vault_file.name}] Usuario: {username}")
        
        conn = sqlite3.connect(vault_file)
        cursor = conn.cursor()
        
        # Contar servicios sin dueño
        cursor.execute("SELECT COUNT(*) FROM secrets WHERE owner_name IS NULL AND deleted = 0")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"  [WARN] Encontrados {count} servicios sin owner_name")
            
            # Actualizar todos los servicios sin dueño
            cursor.execute("""
                UPDATE secrets 
                SET owner_name = ? 
                WHERE owner_name IS NULL
            """, (username,))
            
            conn.commit()
            print(f"  [OK] {count} servicios actualizados con owner_name = '{username}'")
        else:
            print(f"  [OK] Todos los servicios ya tienen owner_name")
        
        conn.close()
    
    print("\n" + "=" * 70)
    print("MIGRACIÓN COMPLETADA")
    print("=" * 70)

if __name__ == "__main__":
    migrate_owner_names()
