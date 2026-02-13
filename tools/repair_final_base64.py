from pathlib import Path
import os
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
"""
Reparacion FINAL - Decodificar correctamente Base64 desde hex
"""
from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY
import sqlite3
from pathlib import Path
import base64

print("=" * 80)
print("REPARACION FINAL - DECODIFICACION CORRECTA")
print("=" * 80)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
response = supabase.table("users").select("*").eq("username", "RODOLFO").execute()

if not response.data:
    print("[ERROR] No se encontro RODOLFO")
    exit(1)

cloud = response.data[0]

def decode_supabase_key(hex_string):
    """
    Supabase guarda: Base64 -> Hex -> Prefijo \\x
    Ejemplo: \\x4b486d... -> 4b486d... (hex) -> KHm8... (base64) -> bytes
    """
    if not hex_string:
        return None
    
    # Remover prefijo \\x
    if hex_string.startswith('\\x'):
        hex_string = hex_string[2:]
    
    # Convertir hex a string ASCII
    try:
        ascii_string = bytes.fromhex(hex_string).decode('ascii')
        print(f"   Decoded to ASCII: {ascii_string[:50]}...")
        
        # Decodificar Base64
        binary_data = base64.b64decode(ascii_string)
        print(f"   Decoded from Base64: {len(binary_data)} bytes")
        return binary_data
    except Exception as e:
        print(f"   [ERROR] Failed to decode: {e}")
        return None

print("\n[1] Decodificando Protected Key...")
pk_bytes = decode_supabase_key(cloud.get('protected_key'))

print("\n[2] Decodificando Wrapped Vault Key...")
wvk_bytes = decode_supabase_key(cloud.get('wrapped_vault_key'))

print("\n[3] Decodificando Vault Salt...")
vs_bytes = decode_supabase_key(cloud.get('vault_salt'))

if not pk_bytes:
    print("\n[ERROR] No se pudo decodificar Protected Key")
    exit(1)

# Guardar en DB local
print("\n[4] Guardando en base de datos local...")
db_path = Path(str(BASE_DIR) + "/data/vault_rodolfo.db")
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

cursor.execute("""
    UPDATE users 
    SET protected_key = ?,
        wrapped_vault_key = ?,
        vault_salt = ?
    WHERE username = 'RODOLFO'
""", (pk_bytes, wvk_bytes, vs_bytes))

conn.commit()

# Verificar
cursor.execute("SELECT protected_key, wrapped_vault_key, vault_salt FROM users WHERE username = 'RODOLFO'")
row = cursor.fetchone()

print("\n[5] Verificacion:")
if row[0]:
    print(f"   Protected Key: {len(row[0])} bytes")
    print(f"   First 16 bytes (hex): {row[0][:16].hex()}")
else:
    print(f"   [ERROR] Protected Key es None")

if row[1]:
    print(f"   Wrapped Vault Key: {len(row[1])} bytes")
else:
    print(f"   [WARN] Wrapped Vault Key es None")

if row[2]:
    print(f"   Vault Salt: {len(row[2])} bytes")
else:
    print(f"   [WARN] Vault Salt es None")

conn.close()

print("\n" + "=" * 80)
print("COMPLETADO - Reinicia la aplicacion")
print("=" * 80)
