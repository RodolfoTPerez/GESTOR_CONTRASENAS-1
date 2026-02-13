from pathlib import Path
import os
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
"""
Script de reparacion para sincronizar las llaves desde Supabase
"""
from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY
import sqlite3
from pathlib import Path
import base64

print("=" * 80)
print("REPARACION DE LLAVES - SINCRONIZACION DESDE SUPABASE")
print("=" * 80)

# Conectar a Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Obtener datos del usuario desde Supabase
print("\n[1] Consultando perfil de RODOLFO en Supabase...")
response = supabase.table("users").select("*").eq("username", "RODOLFO").execute()

if not response.data or len(response.data) == 0:
    print("[ERROR] No se encontro el usuario RODOLFO en Supabase")
    exit(1)

cloud_profile = response.data[0]
print(f"[OK] Perfil encontrado en Supabase")
print(f"   Username: {cloud_profile.get('username')}")
print(f"   Role: {cloud_profile.get('role')}")
print(f"   Vault ID: {cloud_profile.get('vault_id')}")

# Verificar llaves en Supabase
print(f"\n[2] Verificando llaves en Supabase...")

protected_key_cloud = cloud_profile.get('protected_key')
if protected_key_cloud:
    print(f"   [OK] Protected Key encontrada en Supabase")
else:
    print(f"   [ERROR] Protected Key NO encontrada en Supabase")
    print(f"   [INFO] Esto significa que las llaves nunca se subieron a la nube")
    print(f"   [INFO] Necesitas regenerar las llaves o recuperarlas de un backup")
    exit(1)

wrapped_vault_key_cloud = cloud_profile.get('wrapped_vault_key')
if wrapped_vault_key_cloud:
    print(f"   [OK] Wrapped Vault Key encontrada en Supabase")
else:
    print(f"   [WARN] Wrapped Vault Key NO encontrada en Supabase")

vault_salt_cloud = cloud_profile.get('vault_salt')
if vault_salt_cloud:
    print(f"   [OK] Vault Salt encontrado en Supabase")
else:
    print(f"   [WARN] Vault Salt NO encontrado en Supabase")

# Conectar a la base de datos local
print(f"\n[3] Actualizando base de datos local...")
db_path = Path(str(BASE_DIR) + "/data/vault_rodolfo.db")
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Convertir las llaves de formato Supabase (bytea hex) a bytes
def convert_bytea_to_bytes(bytea_str):
    if not bytea_str:
        return None
    if isinstance(bytea_str, str) and bytea_str.startswith('\\\\x'):
        return bytes.fromhex(bytea_str[2:])
    elif isinstance(bytea_str, str):
        try:
            return base64.b64decode(bytea_str)
        except:
            return bytea_str.encode('utf-8')
    return bytea_str

protected_key_bytes = convert_bytea_to_bytes(protected_key_cloud)
wrapped_vault_key_bytes = convert_bytea_to_bytes(wrapped_vault_key_cloud)
vault_salt_bytes = convert_bytea_to_bytes(vault_salt_cloud)

# Actualizar el registro del usuario
cursor.execute("""
    UPDATE users 
    SET protected_key = ?,
        wrapped_vault_key = ?,
        vault_salt = ?
    WHERE username = 'RODOLFO'
""", (protected_key_bytes, wrapped_vault_key_bytes, vault_salt_bytes))

conn.commit()

# Verificar la actualizacion
cursor.execute("SELECT protected_key, wrapped_vault_key, vault_salt FROM users WHERE username = 'RODOLFO'")
updated = cursor.fetchone()

print(f"\n[4] Verificando actualizacion...")
if updated[0]:
    print(f"   [OK] Protected Key actualizada: {len(updated[0])} bytes")
else:
    print(f"   [ERROR] Protected Key sigue MISSING")

if updated[1]:
    print(f"   [OK] Wrapped Vault Key actualizada: {len(updated[1])} bytes")
else:
    print(f"   [WARN] Wrapped Vault Key sigue MISSING")

if updated[2]:
    print(f"   [OK] Vault Salt actualizado: {len(updated[2])} bytes")
else:
    print(f"   [WARN] Vault Salt sigue MISSING")

conn.close()

print("\n" + "=" * 80)
print("REPARACION COMPLETADA")
print("=" * 80)
print("\n[SIGUIENTE PASO] Reinicia la aplicacion y vuelve a iniciar sesion")
