from pathlib import Path
import os
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
import os
import requests
import sqlite3
import base64
import secrets
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from dotenv import load_dotenv

load_dotenv(str(BASE_DIR) + "/.env")
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

def fix_identidad_definitiva():
    print("="*60)
    print("REPARACIÓN DE LLAVES Y TOTP (GRADO SENIOR)")
    print("="*60)
    
    import getpass
    password = getpass.getpass("Ingrese contraseña para FIX DEFINITION: ")
    username = "RODOLFO"
    vault_id = "0637ae0d-7446-4c94-bc06-18c918ce596e"
    totp_limpio = "JBSWY3DPEHPK3PXP" # 16 caracteres exactos
    
    # 1. Re-generar Criptografía con Alineación Perfecta (NUEVA POLÍTICA UNIFICADA)
    # Importamos CryptoEngine de la propia App para garantizar coherencia
    if str(BASE_DIR) not in sys.path: sys.path.append(str(BASE_DIR))
    from src.infrastructure.crypto_engine import CryptoEngine
    
    # Generar Hash de Password (Standard 100k, Salt Binario Real)
    pwd_hash, salt_bin = CryptoEngine.hash_user_password(password)
    salt_pwd_str = salt_bin.hex()
    
    # Salt de Bóveda (Binary)
    v_salt_bin = os.urandom(16)
    
    # Generar Master Key (32 bytes)
    master_key = CryptoEngine.generate_vault_master_key()
    
    # Envolver llave (Personal Key) usando CryptoEngine
    protected_key = CryptoEngine.wrap_vault_key(master_key, password, v_salt_bin)
    
    # Envolver llave de Bóveda (Vault Key) - Espejo para este admin
    wrapped_vault = protected_key
    
    # 2. ACTUALIZAR SUPABASE
    headers = {
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json",
        "x-guardian-user": username
    }
    
    # Forzamos los tipos correctos para evitar que Supabase los interprete mal
    cloud_payload = {
        "password_hash": pwd_hash,
        "salt": salt_pwd_str,
        "vault_salt": base64.b64encode(v_salt_bin).decode(),
        "protected_key": base64.b64encode(protected_key).decode(),
        "wrapped_vault_key": base64.b64encode(wrapped_vault).decode(),
        "totp_secret": totp_limpio, 
        "vault_id": vault_id
    }
    
    print(f"\n[1/2] Sincronizando Nube (Identity & Keys)...")
    r = requests.patch(f"{URL}/rest/v1/users?username=eq.{username}", headers=headers, json=cloud_payload)
    
    # 3. ACTUALIZAR LOCALMENTE (vault_rodolfo.db)
    db_u = str(BASE_DIR) + "/data/vault_rodolfo.db"
    conn = sqlite3.connect(db_u)
    conn.execute("DELETE FROM users WHERE UPPER(username) = ?", (username,))
    
    cols = "username, password_hash, salt, vault_salt, role, active, protected_key, vault_id, totp_secret, wrapped_vault_key"
    vals = (
        username, 
        pwd_hash, 
        salt_pwd_str, 
        sqlite3.Binary(v_salt_bin), 
        "admin", 
        1, 
        sqlite3.Binary(protected_key), 
        vault_id, 
        totp_limpio,
        sqlite3.Binary(wrapped_vault)
    )
    
    conn.execute(f"INSERT INTO users ({cols}) VALUES (?,?,?,?,?,?,?,?,?,?)", vals)
    conn.commit()
    conn.close()
    print("[2/2] Sincronizando Base de Datos Local...")

    print("\n" + "="*60)
    print("REPARACIÓN FINALIZADA")
    print("Estado esperado: PersonalKey=READY, VaultKey=READY")
    print("="*60)

if __name__ == "__main__":
    fix_identidad_definitiva()
