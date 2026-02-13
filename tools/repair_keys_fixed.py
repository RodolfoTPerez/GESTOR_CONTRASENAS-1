from pathlib import Path
import os
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
"""
Reparacion CORRECTA - Convertir las llaves de Supabase a formato binario correcto
"""
from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY
import sqlite3
from pathlib import Path
import base64

print("=" * 80)
print("REPARACION CORRECTA DE LLAVES")
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
print(f"[OK] Perfil encontrado")

# Funcion mejorada para convertir bytea de PostgreSQL a bytes de Python
def convert_supabase_bytea_to_bytes(value):
    """
    Convierte el formato bytea de Supabase a bytes de Python
    Supabase devuelve bytea como string con formato \\xHEXHEXHEX
    """
    if not value:
        return None
    
    if isinstance(value, bytes):
        # Ya es bytes, perfecto
        return value
    
    if isinstance(value, str):
        # Formato bytea de PostgreSQL: \\xHEXHEXHEX
        if value.startswith('\\\\x'):
            try:
                # Remover el prefijo \\x y convertir hex a bytes
                hex_string = value[2:]  # Remover \\x
                return bytes.fromhex(hex_string)
            except Exception as e:
                print(f"   [WARN] Error convirtiendo desde \\\\x format: {e}")
        
        # Intentar Base64
        try:
            return base64.b64decode(value)
        except:
            pass
        
        # Si todo falla, convertir string a bytes UTF-8
        return value.encode('utf-8')
    
    return None

# Convertir las llaves
print("\n[2] Convirtiendo llaves desde Supabase...")

protected_key_cloud = cloud_profile.get('protected_key')
protected_key_bytes = convert_supabase_bytea_to_bytes(protected_key_cloud)

if protected_key_bytes:
    print(f"   [OK] Protected Key: {len(protected_key_bytes)} bytes")
else:
    print(f"   [ERROR] Protected Key no se pudo convertir")
    print(f"   Valor original: {repr(protected_key_cloud)[:100]}")

wrapped_vault_key_cloud = cloud_profile.get('wrapped_vault_key')
wrapped_vault_key_bytes = convert_supabase_bytea_to_bytes(wrapped_vault_key_cloud)

if wrapped_vault_key_bytes:
    print(f"   [OK] Wrapped Vault Key: {len(wrapped_vault_key_bytes)} bytes")
else:
    print(f"   [WARN] Wrapped Vault Key no se pudo convertir")

vault_salt_cloud = cloud_profile.get('vault_salt')
vault_salt_bytes = convert_supabase_bytea_to_bytes(vault_salt_cloud)

if vault_salt_bytes:
    print(f"   [OK] Vault Salt: {len(vault_salt_bytes)} bytes")
else:
    print(f"   [WARN] Vault Salt no se pudo convertir")

# Conectar a la base de datos local
print(f"\n[3] Actualizando base de datos local...")
db_path = Path(str(BASE_DIR) + "/data/vault_rodolfo.db")
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Actualizar con BLOB binario correcto
cursor.execute("""
    UPDATE users 
    SET protected_key = ?,
        wrapped_vault_key = ?,
        vault_salt = ?
    WHERE username = 'RODOLFO'
""", (
    sqlite3.Binary(protected_key_bytes) if protected_key_bytes else None,
    sqlite3.Binary(wrapped_vault_key_bytes) if wrapped_vault_key_bytes else None,
    sqlite3.Binary(vault_salt_bytes) if vault_salt_bytes else None
))

conn.commit()

# Verificar
cursor.execute("SELECT protected_key, wrapped_vault_key, vault_salt FROM users WHERE username = 'RODOLFO'")
updated = cursor.fetchone()

print(f"\n[4] Verificacion final...")
if updated[0]:
    print(f"   [OK] Protected Key guardada: {len(updated[0])} bytes (tipo: {type(updated[0])})")
else:
    print(f"   [ERROR] Protected Key sigue siendo None")

if updated[1]:
    print(f"   [OK] Wrapped Vault Key guardada: {len(updated[1])} bytes (tipo: {type(updated[1])})")
else:
    print(f"   [WARN] Wrapped Vault Key es None")

if updated[2]:
    print(f"   [OK] Vault Salt guardado: {len(updated[2])} bytes (tipo: {type(updated[2])})")
else:
    print(f"   [WARN] Vault Salt es None")

conn.close()

print("\n" + "=" * 80)
print("REPARACION COMPLETADA")
print("=" * 80)
print("\n[SIGUIENTE PASO] Reinicia la aplicacion: python main.py")
