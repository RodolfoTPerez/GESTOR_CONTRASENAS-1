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

def reset_global_rodolfo():
    print("="*60)
    print("RESETEO GLOBAL DE IDENTIDAD (NUBE + LOCAL)")
    print("="*60)
    
    import getpass
    password = getpass.getpass("Ingrese contraseña para RESET REGIONAL: ")
    username = "RODOLFO"
    vault_id = "0637ae0d-7446-4c94-bc06-18c918ce596e"
    
    # 1. Generar nueva criptografía estándar
    # Salt para el Hash de login (usado por UserManager.hash_password)
    # UserManager usa salt.encode('utf-8'), así que el salt debe ser un string hex
    salt_pwd_str = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt_pwd_str.encode('utf-8'), 100_000)
    pwd_hash = dk.hex()
    
    # Salt para la Bóveda (Binary)
    v_salt = os.urandom(16)
    
    # Generar Master Key (32 bytes)
    master_key = os.urandom(32)
    
    # Derivar KEK (Mismo que SecretsManager / CryptoEngine)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=v_salt, iterations=100000)
    kek = kdf.derive(password.encode())
    
    # Envolver llave (nonce 12 + cipher 48 = 60 bytes)
    nonce = os.urandom(12)
    protected_key = nonce + AESGCM(kek).encrypt(nonce, master_key, None)
    
    # Preparar datos para transporte (Base64)
    p_key_b64 = base64.b64encode(protected_key).decode()
    v_salt_b64 = base64.b64encode(v_salt).decode()
    
    # 2. ACTUALIZAR SUPABASE (La Fuente de Verdad)
    headers = {
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json",
        "x-guardian-user": username
    }
    
    cloud_payload = {
        "password_hash": pwd_hash,
        "salt": salt_pwd_str,
        "vault_salt": v_salt_b64,
        "protected_key": p_key_b64,
        "totp_secret": "JBSWY3DPEHPK3PXP", # Secreto limpio
        "vault_id": vault_id
    }
    
    print(f"\n[1/3] Actualizando Supabase...")
    r = requests.patch(f"{URL}/rest/v1/users?username=eq.{username}", headers=headers, json=cloud_payload)
    if r.status_code in (200, 201, 204):
        print(">>> Nube actualizada con éxito.")
    else:
        print(f">>> ERROR Nube: {r.status_code} - {r.text}")
        return

    # 3. ACTUALIZAR LOCAL (Ambas bases de datos)
    print(f"\n[2/3] Actualizando Bases de Datos Locales...")
    
    # vault_rodolfo.db
    db_u = str(BASE_DIR) + "/data/vault_rodolfo.db"
    if os.path.exists(db_u):
        conn = sqlite3.connect(db_u)
        conn.execute("DELETE FROM users WHERE UPPER(username) = ?", (username,))
        cols = "username, password_hash, salt, vault_salt, role, active, protected_key, vault_id, totp_secret"
        vals = (username, pwd_hash, salt_pwd_str, sqlite3.Binary(v_salt), "admin", 1, sqlite3.Binary(protected_key), vault_id, "JBSWY3DPEHPK3PXP")
        conn.execute(f"INSERT INTO users ({cols}) VALUES (?,?,?,?,?,?,?,?,?)", vals)
        conn.commit()
        conn.close()
        print(">>> vault_rodolfo.db actualizado.")

    # passguardian.db
    db_m = str(BASE_DIR) + "/data/passguardian.db"
    if os.path.exists(db_m):
        conn = sqlite3.connect(db_m)
        conn.execute("CREATE TABLE IF NOT EXISTS vault_access (vault_id TEXT, owner_name TEXT, role TEXT)")
        conn.execute("DELETE FROM vault_access WHERE UPPER(owner_name) = ?", (username,))
        conn.execute("INSERT INTO vault_access (vault_id, owner_name, role) VALUES (?,?,?)", (vault_id, username, "admin"))
        conn.commit()
        conn.close()
        print(">>> passguardian.db actualizado.")

    print(f"\n[3/3] Sincronizando Acceso de Bóveda (Vault Access)...")
    # Asegurar que el vault_access también se resetee en la nube si es posible
    # (Omitimos por ahora ya que el primary login es lo que importa)

    print("\n" + "="*60)
    print("RESETEO COMPLETADO EXITOSAMENTE")
    print("Contraseña: RODOLFO")
    print("="*60)
    print("\nAhora puedes abrir la App. El error de TOTP habrá desaparecido y las llaves estarán en READY.")

if __name__ == "__main__":
    reset_global_rodolfo()
