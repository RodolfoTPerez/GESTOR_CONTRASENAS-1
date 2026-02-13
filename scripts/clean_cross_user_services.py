"""
Script de Limpieza: Eliminar servicios privados de otros usuarios
===================================================================
Este script elimina de cada base de datos local los servicios privados
que NO pertenecen al usuario de esa bóveda.
"""

import sqlite3
from pathlib import Path

def clean_cross_user_private_services():
    """Elimina servicios privados que no pertenecen al usuario de la bóveda."""
    
    data_dir = Path("data")
    vault_files = list(data_dir.glob("vault_*.db"))
    
    print("=" * 70)
    print("LIMPIEZA: Eliminando servicios privados de otros usuarios")
    print("=" * 70)
    
    total_deleted = 0
    
    for vault_file in vault_files:
        # Extraer el nombre del usuario desde el nombre del archivo
        username = vault_file.stem.replace("vault_", "").upper()
        
        print(f"\n[DB: {vault_file.name}] Usuario: {username}")
        
        conn = sqlite3.connect(vault_file)
        cursor = conn.cursor()
        
        # Encontrar servicios privados que NO pertenecen a este usuario
        cursor.execute("""
            SELECT id, service, owner_name 
            FROM secrets 
            WHERE is_private = 1 
            AND (owner_name != ? OR owner_name IS NULL)
            AND deleted = 0
        """, (username,))
        
        foreign_services = cursor.fetchall()
        
        if foreign_services:
            print(f"  [WARN] Encontrados {len(foreign_services)} servicios privados de otros usuarios:")
            for sid, service, owner in foreign_services:
                owner_display = owner if owner else "NULL"
                print(f"    - ID {sid}: {service} (owner: {owner_display})")
            
            # Eliminar estos servicios
            cursor.execute("""
                DELETE FROM secrets 
                WHERE is_private = 1 
                AND (owner_name != ? OR owner_name IS NULL)
            """, (username,))
            
            conn.commit()
            deleted_count = cursor.rowcount
            total_deleted += deleted_count
            print(f"  [OK] {deleted_count} servicios privados eliminados")
        else:
            print(f"  [OK] No hay servicios privados de otros usuarios")
        
        conn.close()
    
    print("\n" + "=" * 70)
    print(f"LIMPIEZA COMPLETADA - {total_deleted} servicios eliminados en total")
    print("=" * 70)

if __name__ == "__main__":
    clean_cross_user_private_services()
