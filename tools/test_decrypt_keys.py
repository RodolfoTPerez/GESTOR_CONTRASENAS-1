from pathlib import Path
import os
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
"""
Diagnostico del proceso de descifrado de llaves
Simula lo que hace set_active_user para ver donde falla
"""
import sqlite3
from pathlib import Path
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

# Conectar a la DB
db_path = Path(str(BASE_DIR) + "/data/vault_rodolfo.db")
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 80)
print("DIAGNOSTICO DEL PROCESO DE DESCIFRADO DE LLAVES")
print("=" * 80)

# Obtener perfil
cursor.execute("SELECT * FROM users WHERE username = 'RODOLFO'")
user = cursor.fetchone()
columns = [desc[0] for desc in cursor.description]
profile = dict(zip(columns, user))

print("\n[1] DATOS DEL PERFIL:")
print(f"   Username: {profile.get('username')}")
print(f"   Vault ID: {profile.get('vault_id')}")

# Verificar vault_salt
vault_salt = profile.get('vault_salt')
if vault_salt and isinstance(vault_salt, bytes):
    salt_hash = hashlib.md5(vault_salt).hexdigest()[:8].upper()
    print(f"   Vault Salt: {len(vault_salt)} bytes (Hash: {salt_hash})")
else:
    print(f"   [ERROR] Vault Salt invalido: {type(vault_salt)}")
    exit(1)

# Verificar protected_key
protected_key = profile.get('protected_key')
if protected_key and isinstance(protected_key, bytes):
    print(f"   Protected Key (cifrada): {len(protected_key)} bytes")
    print(f"   Primeros 16 bytes: {protected_key[:16].hex()}")
else:
    print(f"   [ERROR] Protected Key invalida: {type(protected_key)}")
    exit(1)

# Verificar wrapped_vault_key
wrapped_vault_key = profile.get('wrapped_vault_key')
if wrapped_vault_key and isinstance(wrapped_vault_key, bytes):
    print(f"   Wrapped Vault Key (cifrada): {len(wrapped_vault_key)} bytes")
else:
    print(f"   [ERROR] Wrapped Vault Key invalida: {type(wrapped_vault_key)}")

# Solicitar contraseña
print("\n[2] INGRESA LA CONTRASEÑA DE RODOLFO:")
password = input("   Password: ")

if not password:
    print("[ERROR] Contraseña vacia")
    exit(1)

# Derivar KEK (Key Encryption Key)
print("\n[3] DERIVANDO KEK (Key Encryption Key)...")
try:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=vault_salt,
        iterations=100000,
        backend=default_backend()
    )
    kek = kdf.derive(password.encode('utf-8'))
    print(f"   [OK] KEK derivada: {len(kek)} bytes")
    print(f"   KEK (primeros 16 bytes): {kek[:16].hex()}")
except Exception as e:
    print(f"   [ERROR] No se pudo derivar KEK: {e}")
    exit(1)

# Intentar descifrar Protected Key
print("\n[4] DESCIFRANDO PROTECTED KEY...")
try:
    # La Protected Key debe tener al menos 28 bytes (12 nonce + 16 datos minimo)
    if len(protected_key) < 28:
        print(f"   [ERROR] Protected Key muy corta: {len(protected_key)} bytes")
        exit(1)
    
    # Extraer nonce (primeros 12 bytes) y ciphertext (resto)
    nonce = protected_key[:12]
    ciphertext = protected_key[12:]
    
    print(f"   Nonce: {nonce.hex()}")
    print(f"   Ciphertext: {len(ciphertext)} bytes")
    
    # Descifrar
    cipher = AESGCM(kek)
    personal_key = cipher.decrypt(nonce, ciphertext, None)
    
    print(f"   [OK] Personal Key descifrada: {len(personal_key)} bytes")
    print(f"   Personal Key (primeros 16 bytes): {personal_key[:16].hex()}")
    
except Exception as e:
    print(f"   [ERROR] No se pudo descifrar Protected Key: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Intentar descifrar Wrapped Vault Key
print("\n[5] DESCIFRANDO WRAPPED VAULT KEY...")
try:
    if len(wrapped_vault_key) < 28:
        print(f"   [ERROR] Wrapped Vault Key muy corta: {len(wrapped_vault_key)} bytes")
    else:
        nonce = wrapped_vault_key[:12]
        ciphertext = wrapped_vault_key[12:]
        
        cipher = AESGCM(kek)
        vault_key = cipher.decrypt(nonce, ciphertext, None)
        
        print(f"   [OK] Vault Key descifrada: {len(vault_key)} bytes")
        print(f"   Vault Key (primeros 16 bytes): {vault_key[:16].hex()}")
        
except Exception as e:
    print(f"   [ERROR] No se pudo descifrar Wrapped Vault Key: {e}")
    import traceback
    traceback.print_exc()

conn.close()

print("\n" + "=" * 80)
print("DIAGNOSTICO COMPLETADO")
print("=" * 80)
print("\n[CONCLUSION]")
print("Si ambas llaves se descifraron correctamente, el problema esta en el codigo")
print("de set_active_user que no esta usando la logica correcta.")
