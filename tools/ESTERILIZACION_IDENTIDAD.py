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

def limpieza_profunda_identidad():
    print("="*60)
    print("OPERACION: ESTERILIZACION DE IDENTIDAD - RODOLFO")
    print("="*60)
    
    import getpass
    password = getpass.getpass("Ingrese contraseña para ESTERILIZACIÓN: ")
    username = "RODOLFO"
    vault_id = "0637ae0d-7446-4c94-bc06-18c918ce596e"
    totp_limpio = "JBSWY3DPEHPK3PXP" # 16 chars Base32 puro
    
    # 1. Generar Criptografía Maestra Estándar
    # Salt de contraseña (es un hex string para UserManager)
    salt_pwd_str = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt_pwd_str.encode('utf-8'), 100000)
    pwd_hash = dk.hex()
    
    # Salt de Bóveda (Binary 16 bytes)
    v_salt = os.urandom(16)
    
    # Llave Maestra (32 bytes)
    master_key = os.urandom(32)
    
    # Derivar KEK (PBKDF2-HMAC-SHA256, 100k)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=v_salt, iterations=100000)
    kek = kdf.derive(password.encode('utf-8'))
    
    # Envolver llaves (Nonce 12 + Cipher 32 + Tag 16 = 60 bytes)
    nonce = os.urandom(12)
    p_key = nonce + AESGCM(kek).encrypt(nonce, master_key, None)
    
    # 2. LIMPIAR SUPABASE (Para que no nos sobreescriba con basura)
    headers = {
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json",
        "x-guardian-user": username,
        "Prefer": "return=minimal"
    }
    
    # En Supabase guardamos como Base64 para el transporte seguro
    cloud_payload = {
        "password_hash": pwd_hash,
        "salt": salt_pwd_str,
        "vault_salt": base64.b64encode(v_salt).decode(),
        "protected_key": base64.b64encode(p_key).decode(),
        "wrapped_vault_key": base64.b64encode(p_key).decode(), # Espejo para este caso
        "totp_secret": totp_limpio, 
        "vault_id": vault_id
    }
    
    print(f"[1/2] Esterilizando perfil en Supabase...")
    r = requests.patch(f"{URL}/rest/v1/users?username=eq.{username}", headers=headers, json=cloud_payload)
    if r.status_code not in (200, 204):
        print(f"!!! Error en Nube: {r.status_code} {r.text}")
        return

    # 3. LIMPIAR LOCAL (vault_rodolfo.db)
    # Aquí es donde vamos a forzar el guardado BINARIO para que no haya dudas
    db_path = str(BASE_DIR) + "/data/vault_rodolfo.db"
    conn = sqlite3.connect(db_path)
    # IMPORTANTE: Eliminamos el registro viejo para asegurar que la inserción sea limpia
    conn.execute("DELETE FROM users WHERE UPPER(username) = 'RODOLFO'")
    
    cols = "username, password_hash, salt, vault_salt, role, active, protected_key, vault_id, totp_secret, wrapped_vault_key"
    vals = (
        username, 
        pwd_hash, 
        salt_pwd_str, 
        sqlite3.Binary(v_salt), 
        "admin", 
        1, 
        sqlite3.Binary(p_key), 
        vault_id, 
        totp_limpio,
        sqlite3.Binary(p_key)
    )
    
    conn.execute(f"INSERT INTO users ({cols}) VALUES (?,?,?,?,?,?,?,?,?,?)", vals)
    conn.commit()
    conn.close()
    print("[2/2] Base de datos local reconstruida.")

    print("\n" + "="*60)
    print("SISTEMA ESTERILIZADO Y LISTO")
    print("Contraseña: RODOLFO")
    print("="*60)

if __name__ == "__main__":
    limpieza_profunda_identidad()
