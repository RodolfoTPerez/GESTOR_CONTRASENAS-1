from pathlib import Path
import os
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
"""
Reparacion DEFINITIVA - Decodificar correctamente el formato bytea de PostgreSQL
"""
from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY
import sqlite3
from pathlib import Path

print("=" * 80)
print("REPARACION DEFINITIVA DE LLAVES")
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

# Funcion CORRECTA para decodificar bytea de PostgreSQL
def decode_postgres_bytea(bytea_string):
    r"""
    PostgreSQL devuelve bytea como string con formato: \xHEXHEXHEX
    Ejemplo: '\x4b486d38347a52' -> bytes
    """
    if not bytea_string:
        return None
    
    if isinstance(bytea_string, bytes):
        # Si ya es bytes, verificar si es texto que necesita decodificacion
        try:
            bytea_string = bytea_string.decode('utf-8')
        except:
            return bytea_string
    
    if isinstance(bytea_string, str):
        # Formato bytea de PostgreSQL puede ser \\x o \x
        prefix_to_remove = 0
        if bytea_string.startswith('\\\\x'):
            prefix_to_remove = 2  # Remover \\x
        elif bytea_string.startswith('\\x'):
            prefix_to_remove = 2  # Remover \x
        elif bytea_string.startswith('0x'):
            prefix_to_remove = 2  # Remover 0x
        
        if prefix_to_remove > 0:
            try:
                # Remover el prefijo y convertir hex a bytes
                hex_string = bytea_string[prefix_to_remove:]
                return bytes.fromhex(hex_string)
            except Exception as e:
                print(f"   [ERROR] No se pudo decodificar bytea: {e}")
                print(f"   Valor: {repr(bytea_string[:50])}...")
                return None
    
    return None

# Obtener y decodificar las llaves
print("\n[2] Decodificando llaves desde Supabase...")

protected_key_raw = cloud_profile.get('protected_key')
print(f"   Protected Key raw type: {type(protected_key_raw)}")
if isinstance(protected_key_raw, str):
    print(f"   Protected Key raw value (primeros 50): {protected_key_raw[:50]}")

protected_key_bytes = decode_postgres_bytea(protected_key_raw)
if protected_key_bytes:
    print(f"   [OK] Protected Key decodificada: {len(protected_key_bytes)} bytes")
    print(f"   Primeros 16 bytes (hex): {protected_key_bytes[:16].hex()}")
else:
    print(f"   [ERROR] No se pudo decodificar Protected Key")
    exit(1)

wrapped_vault_key_raw = cloud_profile.get('wrapped_vault_key')
wrapped_vault_key_bytes = decode_postgres_bytea(wrapped_vault_key_raw)
if wrapped_vault_key_bytes:
    print(f"   [OK] Wrapped Vault Key decodificada: {len(wrapped_vault_key_bytes)} bytes")
else:
    print(f"   [WARN] No se pudo decodificar Wrapped Vault Key")

vault_salt_raw = cloud_profile.get('vault_salt')
vault_salt_bytes = decode_postgres_bytea(vault_salt_raw)
if vault_salt_bytes:
    print(f"   [OK] Vault Salt decodificado: {len(vault_salt_bytes)} bytes")
else:
    print(f"   [WARN] No se pudo decodificar Vault Salt")

# Actualizar base de datos local
print(f"\n[3] Guardando en base de datos local...")
db_path = Path(str(BASE_DIR) + "/data/vault_rodolfo.db")
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Guardar como BLOB binario
cursor.execute("""
    UPDATE users 
    SET protected_key = ?,
        wrapped_vault_key = ?,
        vault_salt = ?
    WHERE username = 'RODOLFO'
""", (
    protected_key_bytes,
    wrapped_vault_key_bytes,
    vault_salt_bytes
))

conn.commit()

# Verificar
cursor.execute("SELECT protected_key, wrapped_vault_key, vault_salt FROM users WHERE username = 'RODOLFO'")
updated = cursor.fetchone()

print(f"\n[4] Verificacion final...")
if updated[0]:
    print(f"   [OK] Protected Key: {len(updated[0])} bytes")
    print(f"   Primeros 16 bytes (hex): {updated[0][:16].hex()}")
    print(f"   Tipo: {type(updated[0])}")
else:
    print(f"   [ERROR] Protected Key es None")

if updated[1]:
    print(f"   [OK] Wrapped Vault Key: {len(updated[1])} bytes")
else:
    print(f"   [WARN] Wrapped Vault Key es None")

if updated[2]:
    print(f"   [OK] Vault Salt: {len(updated[2])} bytes")
else:
    print(f"   [WARN] Vault Salt es None")

conn.close()

print("\n" + "=" * 80)
print("REPARACION COMPLETADA")
print("=" * 80)
print("\n[SIGUIENTE PASO] Reinicia la aplicacion: python main.py")
