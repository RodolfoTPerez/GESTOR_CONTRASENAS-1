"""
Script para restaurar la contraseña de RODOLFO
"""
import sqlite3
import hashlib
from pathlib import Path

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Conectar a la base de datos
db_path = Path(r"C:\PassGuardian_v2\data\passguardian.db")
conn = sqlite3.connect(db_path)

# Restaurar contraseña de RODOLFO
new_password = "RODOLFO"
hashed = hash_password(new_password)

conn.execute("UPDATE users SET password_hash = ? WHERE username = 'RODOLFO'", (hashed,))
conn.commit()
conn.close()

print("[OK] Contrasena de RODOLFO restaurada a: RODOLFO")
print("Ahora puedes iniciar sesion")
