from pathlib import Path
import os
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
"""
Script de diagnostico para verificar las llaves de cifrado del usuario RODOLFO
"""
import sqlite3
import base64
from pathlib import Path

# Conectar a la base de datos del usuario
db_path = Path(str(BASE_DIR) + "/data/vault_rodolfo.db")

if not db_path.exists():
    print(f"[ERROR] No existe la base de datos: {db_path}")
    exit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 80)
print("DIAGNOSTICO DE LLAVES DE CIFRADO - RODOLFO")
print("=" * 80)

# Verificar perfil de usuario
cursor.execute("SELECT * FROM users WHERE username = 'RODOLFO'")
user = cursor.fetchone()

if not user:
    print("[ERROR] No se encontro el usuario RODOLFO en la base de datos local")
    conn.close()
    exit(1)

# Obtener nombres de columnas
columns = [desc[0] for desc in cursor.description]
user_dict = dict(zip(columns, user))

print(f"\n[PERFIL DE USUARIO]")
print(f"   Username: {user_dict.get('username')}")
print(f"   Role: {user_dict.get('role')}")
print(f"   Vault ID: {user_dict.get('vault_id')}")
print(f"   User ID: {user_dict.get('user_id')}")

print(f"\n[ESTADO DE LLAVES]")

# Verificar vault_salt
vault_salt = user_dict.get('vault_salt')
if vault_salt:
    if isinstance(vault_salt, bytes):
        print(f"   [OK] Vault Salt: {len(vault_salt)} bytes - {vault_salt[:8].hex()}...")
    else:
        print(f"   [WARN] Vault Salt: Tipo inesperado ({type(vault_salt)})")
else:
    print(f"   [ERROR] Vault Salt: MISSING")

# Verificar protected_key (Personal Key / SVK)
protected_key = user_dict.get('protected_key')
if protected_key:
    if isinstance(protected_key, bytes):
        print(f"   [OK] Protected Key (SVK): {len(protected_key)} bytes - {protected_key[:8].hex()}...")
    else:
        print(f"   [WARN] Protected Key: Tipo inesperado ({type(protected_key)})")
else:
    print(f"   [ERROR] Protected Key (SVK): MISSING")

# Verificar wrapped_vault_key (Team Key)
wrapped_vault_key = user_dict.get('wrapped_vault_key')
if wrapped_vault_key:
    if isinstance(wrapped_vault_key, bytes):
        print(f"   [OK] Wrapped Vault Key: {len(wrapped_vault_key)} bytes - {wrapped_vault_key[:8].hex()}...")
    else:
        print(f"   [WARN] Wrapped Vault Key: Tipo inesperado ({type(wrapped_vault_key)})")
else:
    print(f"   [ERROR] Wrapped Vault Key: MISSING")

# Verificar password_hash
password_hash = user_dict.get('password_hash')
if password_hash:
    print(f"   [OK] Password Hash: Presente")
else:
    print(f"   [ERROR] Password Hash: MISSING")

# Verificar salt (password salt)
salt = user_dict.get('salt')
if salt:
    if isinstance(salt, bytes):
        print(f"   [OK] Password Salt: {len(salt)} bytes")
    else:
        print(f"   [WARN] Password Salt: Tipo inesperado ({type(salt)})")
else:
    print(f"   [ERROR] Password Salt: MISSING")

# Verificar vault_access (llaves compartidas)
print(f"\n[VAULT ACCESS - Llaves Compartidas]")
cursor.execute("SELECT * FROM vault_access WHERE username = 'RODOLFO'")
vault_access = cursor.fetchone()

if vault_access:
    va_columns = [desc[0] for desc in cursor.description]
    va_dict = dict(zip(va_columns, vault_access))
    print(f"   [OK] Registro encontrado")
    print(f"   Vault ID: {va_dict.get('vault_id')}")
    
    wrapped_key = va_dict.get('wrapped_key')
    if wrapped_key:
        if isinstance(wrapped_key, bytes):
            print(f"   [OK] Wrapped Key: {len(wrapped_key)} bytes - {wrapped_key[:8].hex()}...")
        else:
            print(f"   [WARN] Wrapped Key: Tipo inesperado ({type(wrapped_key)})")
    else:
        print(f"   [ERROR] Wrapped Key: MISSING")
else:
    print(f"   [WARN] No se encontro registro en vault_access")

# Contar secretos
cursor.execute("SELECT COUNT(*) FROM secrets WHERE deleted = 0")
total_secrets = cursor.fetchone()[0]
print(f"\n[ESTADISTICAS]")
print(f"   Total de secretos activos: {total_secrets}")

cursor.execute("SELECT COUNT(*) FROM secrets WHERE deleted = 0 AND is_private = 1")
private_secrets = cursor.fetchone()[0]
print(f"   Secretos privados: {private_secrets}")

cursor.execute("SELECT COUNT(*) FROM secrets WHERE deleted = 0 AND is_private = 0")
public_secrets = cursor.fetchone()[0]
print(f"   Secretos publicos: {public_secrets}")

print("\n" + "=" * 80)
print("DIAGNOSTICO COMPLETADO")
print("=" * 80)

conn.close()
