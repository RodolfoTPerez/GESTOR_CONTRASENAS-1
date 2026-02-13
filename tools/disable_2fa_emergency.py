"""
Script de emergencia para desactivar 2FA temporalmente
"""
import sqlite3
from pathlib import Path

# Conectar a la base de datos de usuarios
db_path = Path(r"C:\PassGuardian_v2\data\passguardian.db")
conn = sqlite3.connect(db_path)

# Desactivar 2FA para RODOLFO
conn.execute("UPDATE users SET totp_secret = NULL WHERE username = 'RODOLFO'")
conn.commit()
conn.close()

print("[OK] 2FA desactivado para RODOLFO")
print("Ahora puedes iniciar sesion sin codigo 2FA")
print("Despues de entrar, ve a Configuracion y reactiva el 2FA")
