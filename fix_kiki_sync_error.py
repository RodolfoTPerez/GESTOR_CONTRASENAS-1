
import sqlite3
import os
from pathlib import Path

# Configuración
data_dir = Path("c:/PassGuardian_v2/data")
CLOUD_KIKI_ID = "ced3c7c9-c1bc-46a6-891a-cb69c2ed40a4"
db_path = data_dir / "vault_kiki.db"

if not db_path.exists():
    print(f"File not found: {db_path}")
    exit(1)

print(f"--- REPARANDO ALINEACION DE ID PARA KIKI ---")
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# 1. Actualizar el ID del usuario en la tabla users
print(f"Cambiando ID de usuario local a: {CLOUD_KIKI_ID}")
cursor.execute("UPDATE users SET user_id = ? WHERE username = 'KIKI'", (CLOUD_KIKI_ID,))

# 2. Actualizar todos los logs de auditoria pendientes
# Tanto los que tenian el ID "fantasma" como el ID local incorrecto
print(f"Corrigiendo registros de auditoria pendientes...")
cursor.execute("UPDATE security_audit SET user_id = ? WHERE synced = 0", (CLOUD_KIKI_ID,))

conn.commit()
print(f"Registros afectados: {conn.total_changes}")
conn.close()

print("\n--- PROCESO COMPLETADO ---")
print("Ahora la sincronización debería funcionar sin errores 409.")
