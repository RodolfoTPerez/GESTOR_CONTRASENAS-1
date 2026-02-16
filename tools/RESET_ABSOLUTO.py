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

def reset_final_y_limpio():
    print("="*60)
    print("RESETEO ABSOLUTO DE IDENTIDAD - RODOLFO")
    print("="*60)
    
    import getpass
    password = getpass.getpass("Ingrese contraseña para RESET ABSOLUTO: ")
    username = "RODOLFO"
    vault_id = "0637ae0d-7446-4c94-bc06-18c918ce596e"
    
    # IMPORTANTE: Secreo TOTP de 16 caracteres exactos.
    totp_secret = "JBSWY3DPEHPK3PXP" 

    # 1. Criptografía Local
    salt_pwd_str = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt_pwd_str.encode('utf-8'), 100000)
    pwd_hash = dk.hex()
    
    v_salt = os.urandom(16)
    master_key = os.urandom(32)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=v_salt, iterations=100000)
    kek = kdf.derive(password.encode('utf-8'))
    nonce = os.urandom(12)
    p_key = nonce + AESGCM(kek).encrypt(nonce, master_key, None)

    # 2. ACTUALIZAR SUPABASE PRIMERO
    headers = {
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json",
        "x-guardian-user": username,
        "Prefer": "return=minimal"
    }
    
    cloud_payload = {
        "password_hash": pwd_hash,
        "salt": salt_pwd_str,
        "vault_salt": base64.b64encode(v_salt).decode(),
        "protected_key": base64.b64encode(p_key).decode(),
        "wrapped_vault_key": base64.b64encode(p_key).decode(),
        "totp_secret": totp_secret, 
        "vault_id": vault_id,
        "active": True
    }
    
    print("[1/2] Limpiando perfil en la Nube...")
    requests.patch(f"{URL}/rest/v1/users?username=eq.{username}", headers=headers, json=cloud_payload)

    # 3. LIMPIAR LOCAL (Ambos archivos)
    for db in ["vault_rodolfo.db", "passguardian.db"]:
        path = fstr(BASE_DIR) + "/data/{db}"
        if os.path.exists(path):
            os.remove(path)
            print(f"[OK] Archivo {db} eliminado para recreación limpia.")

    # 4. CREAR DB LOCAL NUEVA CON LOS DATOS PERFECTOS
    db_path = str(BASE_DIR) + "/data/vault_rodolfo.db"
    conn = sqlite3.connect(db_path)
    # Crear tabla si no existe (por si el borrado falló o algo)
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password_hash TEXT, salt TEXT, 
        vault_salt BLOB, role TEXT, active BOOLEAN, 
        protected_key BLOB, totp_secret TEXT, vault_id TEXT, 
        wrapped_vault_key BLOB, user_id TEXT)""")
    
    cols = "username, password_hash, salt, vault_salt, role, active, protected_key, totp_secret, vault_id, wrapped_vault_key"
    vals = (username, pwd_hash, salt_pwd_str, sqlite3.Binary(v_salt), "admin", 1, sqlite3.Binary(p_key), totp_secret, vault_id, sqlite3.Binary(p_key))
    
    conn.execute(f"INSERT INTO users ({cols}) VALUES (?,?,?,?,?,?,?,?,?,?)", vals)
    conn.commit()
    conn.close()
    print("[2/2] Base de datos local regenerada con datos READY.")

if __name__ == "__main__":
    reset_final_y_limpio()
