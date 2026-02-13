import sqlite3
import os

db_path = "data/vault_rodolfo.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tablas encontradas: {tables}")
    
    # Buscar la tabla correcta
    for table in tables:
        if 'user' in table.lower() or 'profile' in table.lower():
            print(f"\nIntentando limpiar tabla: {table}")
            try:
                conn.execute(f"UPDATE {table} SET totp_secret = NULL WHERE username = 'RODOLFO'")
                conn.commit()
                print(f"OK - Tabla {table} actualizada")
            except Exception as e:
                print(f"ERROR en {table}: {e}")
    
    conn.close()
else:
    print("Base de datos no encontrada")
