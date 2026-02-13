from pathlib import Path
import os
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
"""
Diagnostico profundo del formato de las llaves
"""
import sqlite3
from pathlib import Path

db_path = Path(str(BASE_DIR) + "/data/vault_rodolfo.db")
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

cursor.execute("SELECT protected_key, wrapped_vault_key, vault_salt FROM users WHERE username = 'RODOLFO'")
row = cursor.fetchone()

print("=" * 80)
print("DIAGNOSTICO PROFUNDO DE FORMATO DE LLAVES")
print("=" * 80)

if row:
    protected_key, wrapped_vault_key, vault_salt = row
    
    print("\n[1] PROTECTED KEY (SVK):")
    print(f"   Tipo: {type(protected_key)}")
    if protected_key:
        print(f"   Longitud: {len(protected_key)}")
        if isinstance(protected_key, bytes):
            print(f"   Primeros 32 bytes (hex): {protected_key[:32].hex()}")
            print(f"   Primeros 32 bytes (repr): {repr(protected_key[:32])}")
        elif isinstance(protected_key, str):
            print(f"   Primeros 64 chars: {protected_key[:64]}")
            starts_with_backslash_x = protected_key.startswith('\\x')
            print(f"   Contiene backslash-x: {starts_with_backslash_x}")
    else:
        print("   [ERROR] Es None o vacio")
    
    print("\n[2] WRAPPED VAULT KEY:")
    print(f"   Tipo: {type(wrapped_vault_key)}")
    if wrapped_vault_key:
        print(f"   Longitud: {len(wrapped_vault_key)}")
        if isinstance(wrapped_vault_key, bytes):
            print(f"   Primeros 32 bytes (hex): {wrapped_vault_key[:32].hex()}")
            print(f"   Primeros 32 bytes (repr): {repr(wrapped_vault_key[:32])}")
        elif isinstance(wrapped_vault_key, str):
            print(f"   Primeros 64 chars: {wrapped_vault_key[:64]}")
            starts_with_backslash_x = wrapped_vault_key.startswith('\\x')
            print(f"   Contiene backslash-x: {starts_with_backslash_x}")
    else:
        print("   [ERROR] Es None o vacio")
    
    print("\n[3] VAULT SALT:")
    print(f"   Tipo: {type(vault_salt)}")
    if vault_salt:
        print(f"   Longitud: {len(vault_salt)}")
        if isinstance(vault_salt, bytes):
            print(f"   Primeros 16 bytes (hex): {vault_salt[:16].hex()}")
            print(f"   Primeros 16 bytes (repr): {repr(vault_salt[:16])}")
        elif isinstance(vault_salt, str):
            print(f"   Primeros 32 chars: {vault_salt[:32]}")
            starts_with_backslash_x = vault_salt.startswith('\\x')
            print(f"   Contiene backslash-x: {starts_with_backslash_x}")
    else:
        print("   [ERROR] Es None o vacio")

    # Intentar convertir si es string
    print("\n[4] INTENTANDO CONVERSION:")
    if isinstance(protected_key, str) and protected_key.startswith('\\x'):
        try:
            # Es formato bytea de PostgreSQL (\\xHEXHEXHEX)
            converted = bytes.fromhex(protected_key[2:])
            print(f"   Protected Key convertida: {len(converted)} bytes")
        except Exception as e:
            print(f"   [ERROR] No se pudo convertir Protected Key: {e}")
    
    if isinstance(wrapped_vault_key, str) and wrapped_vault_key.startswith('\\x'):
        try:
            converted = bytes.fromhex(wrapped_vault_key[2:])
            print(f"   Wrapped Vault Key convertida: {len(converted)} bytes")
        except Exception as e:
            print(f"   [ERROR] No se pudo convertir Wrapped Vault Key: {e}")

conn.close()

print("\n" + "=" * 80)
