#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REGENERAR VAULT KEY PARA RODOLFO (PROFESSIONAL RESET)
======================================================
Versión corregida por AANA para compatibilidad total con el esquema VULTRAX.
"""

import sys
import os
import sqlite3
import secrets
import getpass
import time
from pathlib import Path

# Agregar path del proyecto para importar módulos si fuera necesario
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

print("="*70)
print("🛡️ REGENERAR VAULT KEY: RODOLFO (MODO INTERACTIVO)")
print("="*70)
print()
print("⚠️  ADVERTENCIA:")
print("   Este script regenerará la vault_master_key localmente.")
print("   Los secretos guardados anteriormente en esta bóveda quedarán inaccesibles.")
print()

response = input("¿Confirmas que deseas proceder con el RESET NUCLEAR? (SI/NO): ").strip().upper()
if response != "SI":
    print("❌ Operación cancelada")
    sys.exit(0)

print()

username = "RODOLFO"
db_path = Path(f"data/vault_{username.lower()}.db")

if not db_path.exists():
    # Intento de búsqueda en directorio raíz por si el script se ejecuta en otro lugar
    db_path = Path(f"../data/vault_{username.lower()}.db")
    if not db_path.exists():
         print(f"❌ Base de datos no encontrada: vault_{username.lower()}.db")
         sys.exit(1)

# Conectar
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Obtener datos del usuario (Ajustado al esquema real: user_id en lugar de id)
try:
    cursor.execute("""
        SELECT user_id, username, vault_id, vault_salt, role
        FROM users
        WHERE UPPER(username) = ?
    """, (username.upper(),))
except sqlite3.OperationalError:
    # Fallback por si la base de datos es muy antigua y aún usa 'id'
    cursor.execute("""
        SELECT id, username, vault_id, vault_salt, role
        FROM users
        WHERE UPPER(username) = ?
    """, (username.upper(),))

row = cursor.fetchone()
if not row:
    print(f"❌ Usuario {username} no encontrado en la base de datos actual.")
    conn.close()
    sys.exit(1)

user_id, user_username, vault_id, vault_salt, role = row

print(f"📊 Usuario validado: {user_username}")
print(f"   Role: {role}")
print(f"   Vault ID: {vault_id}")
print()

# Criptografía
def derive_kek(password: str, salt: bytes, iterations: int = 100000) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
        backend=default_backend()
    )
    return kdf.derive(password.encode("utf-8"))

def wrap_key(vault_key: bytes, password: str, salt: bytes) -> bytes:
    kek = derive_kek(password, salt)
    nonce = secrets.token_bytes(12)
    aes_gcm = AESGCM(kek)
    return nonce + aes_gcm.encrypt(nonce, vault_key, None)

# Solicitar contraseña
print("🔐 Ingresa tu contraseña de PassGuardian:")
password = getpass.getpass("Contraseña: ")

if not vault_salt:
    vault_salt = secrets.token_bytes(16)
else:
    if isinstance(vault_salt, str):
        vault_salt = bytes.fromhex(vault_salt)

# PASO 1: Regenerar
print("\n🔑 Generando nueva llave maestra de 256 bits...")
new_vault_master_key = secrets.token_bytes(32)

# PASO 2: Wrap
print("🔒 Encriptando con PBKDF2 (100k iteraciones)...")
wrapped_vault_key = wrap_key(new_vault_master_key, password, vault_salt)

# PASO 3: Actualizar base de datos
print("💾 Guardando cambios en el sistema...")

try:
    # 3.1 Actualizar users
    cursor.execute("""
        UPDATE users
        SET wrapped_vault_key = ?, vault_salt = ?
        WHERE UPPER(username) = ?
    """, (sqlite3.Binary(wrapped_vault_key), sqlite3.Binary(vault_salt), username.upper()))

    # 3.2 Actualizar vault_access (Sin la columna user_id que sobra en local)
    cursor.execute("""
        INSERT OR REPLACE INTO vault_access 
        (vault_id, wrapped_master_key, access_level, updated_at, synced) 
        VALUES (?, ?, 'admin', ?, 0)
    """, (vault_id, sqlite3.Binary(wrapped_vault_key), int(time.time())))

    conn.commit()
    print("✅ Base de datos actualizada con éxito.")
    
except Exception as e:
    print(f"❌ Error de persistencia: {e}")
    conn.rollback()
    conn.close()
    sys.exit(1)

print("\n" + "="*70)
print("🎉 PROCESO FINALIZADO")
print("="*70)
print("✅ La bóveda ha sido reseteada y re-encriptada.")
print("✅ Ya puedes iniciar la aplicación normalmente.")
print()
print("Sugerencia: Ejecuta 'python main.py' para verificar.")
print("="*70)

conn.close()
