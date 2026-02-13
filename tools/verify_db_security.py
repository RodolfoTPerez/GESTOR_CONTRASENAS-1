import sqlite3
import os

def check_integrity(db_path):
    if not os.path.exists(db_path):
        print(f"File not found: {db_path}")
        return

    size_before = os.path.getsize(db_path)
    print(f"--- Análisis de Integrity: {os.path.basename(db_path)} ---")
    print(f"Tamaño actual: {size_before} bytes")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Integrity Check
    cursor.execute("PRAGMA integrity_check;")
    result = cursor.fetchone()[0]
    print(f"Resultado Integrity Check: {result}")

    # 2. Check for freelist pages (pages that are empty but still in the file)
    # VACUUM should make this 0
    cursor.execute("PRAGMA freelist_count;")
    freelist = cursor.fetchone()[0]
    print(f"Páginas en Freelist (espacio no reclamado): {freelist}")

    # 3. Check for specific data consistency
    cursor.execute("SELECT COUNT(*) FROM secrets WHERE is_private = 1")
    privates = cursor.fetchone()[0]
    print(f"Registros privados totales: {privates}")

    # 4. Simular ejecución de VACUUM si hay freelist
    if freelist > 0:
        print("Ejecutando limpiador (VACUUM)...")
        conn.close()
        # Usamos la lógica de la app
        from src.infrastructure.secrets_manager import SecretsManager
        sm = SecretsManager()
        # Mocking enough to target this DB
        sm.db_path = db_path
        sm.conn = sqlite3.connect(db_path)
        sm.cleanup_vault_cache()
        sm.conn.close()

        size_after = os.path.getsize(db_path)
        print(f"Tamaño post-limpieza: {size_after} bytes")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA freelist_count;")
        print(f"Páginas en Freelist después: {cursor.fetchone()[0]}")
    else:
        print("La base de datos ya está optimizada físicamente.")

    conn.close()
    print("-" * 50)

if __name__ == "__main__":
    import sys
    # Add src to path
    sys.path.append(os.getcwd())
    
    dbs = [
        r"c:\PassGuardian_v2\data\vault_rodolfo.db",
        r"c:\PassGuardian_v2\data\vault_kiki.db"
    ]
    for db in dbs:
        check_integrity(db)
