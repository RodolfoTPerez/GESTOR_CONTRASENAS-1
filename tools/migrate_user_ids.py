"""
Script de migración para renumerar IDs y evitar conflictos entre usuarios.
Ejecutar UNA SOLA VEZ con cada usuario logueado.
"""

import sqlite3
from pathlib import Path

def migrate_user_ids(username):
    """Renumera los IDs de un usuario para que estén en su rango único."""
    
    # Conectar a la base de datos del usuario
    db_path = Path(rf"C:\PassGuardian_v2\data\vault_{username.lower()}.db")
    
    if not db_path.exists():
        print(f"[ERROR] No se encontro la base de datos para {username}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Calcular el offset del usuario (mismo algoritmo que en add_secret)
    user_offset = (hash(username.upper()) % 1000) * 1_000_000
    
    print(f"\n{'='*60}")
    print(f"Migrando IDs de {username}")
    print(f"Rango de IDs: {user_offset:,} - {user_offset + 999_999:,}")
    print(f"{'='*60}\n")
    
    # Obtener todos los registros del usuario
    cursor.execute("""
        SELECT id, service, owner_name 
        FROM secrets 
        WHERE owner_name = ?
        ORDER BY id
    """, (username,))
    
    records = cursor.fetchall()
    
    if not records:
        print(f"[OK] {username} no tiene registros para migrar")
        conn.close()
        return
    
    # Renumerar
    new_id = user_offset + 1
    for old_id, service, owner in records:
        if old_id < user_offset or old_id > user_offset + 999_999:
            print(f"[MIGRAR] {service}: ID {old_id} -> {new_id}")
            cursor.execute("UPDATE secrets SET id = ? WHERE id = ?", (new_id, old_id))
            new_id += 1
        else:
            print(f"[OK] {service}: ID {old_id} ya esta en el rango correcto")
    
    conn.commit()
    conn.close()
    print(f"\n[OK] Migracion completada para {username}\n")

if __name__ == "__main__":
    # Migrar RODOLFO
    migrate_user_ids("RODOLFO")
    
    # Migrar KIKI
    migrate_user_ids("KIKI")
    
    print("\n" + "="*60)
    print("MIGRACIÓN COMPLETADA")
    print("="*60)
    print("\nPróximos pasos:")
    print("1. Cierra PassGuardian si está abierto")
    print("2. Inicia sesión con RODOLFO")
    print("3. Presiona SYNC")
    print("4. Cierra sesión")
    print("5. Inicia sesión con KIKI")
    print("6. Presiona SYNC")
    print("\nAhora cada usuario tendrá IDs únicos y no habrá conflictos.")
