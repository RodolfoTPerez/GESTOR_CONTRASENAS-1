"""
Verificar y eliminar 2FA de RODOLFO
"""
import sqlite3
from pathlib import Path

db_path = Path(r"C:\PassGuardian_v2\data\passguardian.db")
conn = sqlite3.connect(db_path)

# Ver estado actual
cursor = conn.execute("SELECT username, totp_secret FROM users WHERE username = 'RODOLFO'")
row = cursor.fetchone()
print(f"Usuario: {row[0]}")
print(f"TOTP Secret actual: {row[1]}")

# Eliminar 2FA
conn.execute("UPDATE users SET totp_secret = NULL WHERE username = 'RODOLFO'")
conn.commit()

# Verificar
cursor = conn.execute("SELECT username, totp_secret FROM users WHERE username = 'RODOLFO'")
row = cursor.fetchone()
print(f"\nDespues de eliminar:")
print(f"Usuario: {row[0]}")
print(f"TOTP Secret: {row[1]}")

conn.close()
print("\n[OK] 2FA eliminado correctamente")
