
import os
import sys
import base64
import uuid
import time
import random
import secrets
import hashlib
from dotenv import load_dotenv
from supabase import create_client
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

# --- CONFIGURACIÓN ---
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
PASS_DEFAULT = "123456"

if not SUPABASE_URL or not SUPABASE_KEY:
    print("X Falta .env")
    exit(1)

sb = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- MOTOR CRIPTO REPLICADO ---
def derive_kek_from_password(password: str, salt: bytes, iterations=100000) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
        backend=default_backend()
    )
    return kdf.derive(password.encode('utf-8'))

def wrap_vault_key(vault_master_key: bytes, user_password: str, user_salt: bytes) -> bytes:
    kek = derive_kek_from_password(user_password, user_salt)
    aes = AESGCM(kek)
    nonce = os.urandom(12)
    ciphertext = aes.encrypt(nonce, vault_master_key, None)
    return nonce + ciphertext

def encrypt_record_payload(key: bytes, plain: str) -> tuple:
    aes = AESGCM(key)
    nonce = os.urandom(12)
    # Importante: encode utf-8
    ciphertext = aes.encrypt(nonce, plain.encode('utf-8'), None)
    return nonce, ciphertext

# --- LOGICA DE USUARIOS ---
def ensure_user(username, vault_id):
    """
    Crea o Actualiza un usuario para que su password sea '123456' y tenga llaves válidas.
    Devuelve: (username, personal_key, vault_key, user_id)
    """
    print(f"   => Reparando identidad de: {username}...")
    
    # 1. Generar llaves maestras nuevas para este usuario
    new_salt = os.urandom(16)
    new_vault_salt = os.urandom(16)
    
    # Llave Personal (SVK) y Llave de Bóveda (VK)
    personal_key = os.urandom(32)
    vault_key = os.urandom(32) # En teoría debería ser compartida, pero para este fix cada uno tendrá la suya válida
    
    # Derivar Hash de Password (para login)
    # PassGuardian usa hashlib.pbkdf2_hmac para el hash de login local, 
    # pero aquí simulamos lo necesario para que el UserManager lo acepte si lo reseteamos.
    # En realidad, solo necesitamos envolver las llaves correctamente.
    
    # Envolver llaves con "123456"
    kek = derive_kek_from_password(PASS_DEFAULT, new_salt) # Salt de login
    
    # Wrap Personal Key
    aes_kek = AESGCM(kek)
    nonce_pk = os.urandom(12)
    wrapped_pk = nonce_pk + aes_kek.encrypt(nonce_pk, personal_key, None)
    
    # Wrap Vault Key (usando vault_salt)
    wrapped_vk = wrap_vault_key(vault_key, PASS_DEFAULT, new_vault_salt)
    
    # Password Hash para la DB (Simulación simple, el login real lo valida)
    # UserManager.hash_password usa pbkdf2_hmac sha256
    pwd_hash = hashlib.pbkdf2_hmac('sha256', PASS_DEFAULT.encode(), new_salt, 100000).hex()
    
    # Actualizar en Supabase
    # Primero buscamos si existe para obtener ID
    u_res = sb.table("users").select("id").eq("username", username).execute()
    
    if not u_res.data:
        # Crear
        payload = {
            "username": username,
            "role": "user",
            "active": True,
            "vault_id": vault_id,
            "password_hash": pwd_hash,
            "salt": new_salt.hex(), # Supabase espera strings usualmente o bytea? La DB es TEXT para salt segun schema
            "vault_salt": base64.b64encode(new_vault_salt).decode('ascii'),
            "protected_key": base64.b64encode(wrapped_pk).decode('ascii'),
            "wrapped_vault_key": base64.b64encode(wrapped_vk).decode('ascii')
        }
        r = sb.table("users").insert(payload).execute()
        user_id = r.data[0]['id']
    else:
        # Actualizar
        user_id = u_res.data[0]['id']
        payload = {
            "password_hash": pwd_hash,
            "salt": new_salt.hex(),
            "vault_salt": base64.b64encode(new_vault_salt).decode('ascii'),
            "protected_key": base64.b64encode(wrapped_pk).decode('ascii'),
            "wrapped_vault_key": base64.b64encode(wrapped_vk).decode('ascii'),
            "vault_id": vault_id
        }
        sb.table("users").update(payload).eq("id", user_id).execute()
        
    print(f"      + Identidad reparada. Password: {PASS_DEFAULT}")
    return personal_key, vault_key, user_id

def generate_valid_records(username, user_id, vault_id, p_key, v_key):
    batch = []
    
    services = ["Netflix", "Spotify", "Amazon", "Google", "Facebook", "Twitter", "LinkedIn", "Github", "Slack", "Zoom"]
    
    print(f"      > Generando 50 Privados (Cifrados con Personal Key)...")
    for i in range(50):
        svc = f"{random.choice(services)} - {random.randint(1000,9999)}"
        sec_plain = f"Pass_{username}_Priv_{i+1}"
        nonce, cipher = encrypt_record_payload(p_key, sec_plain)
        
        # Integridad
        integrity = hashlib.sha256(cipher).hexdigest()
        
        batch.append({
            "id": str(uuid.uuid4()),
            "service": svc,
            "username": f"{username.lower()}@private.com",
            "secret": base64.b64encode(cipher).decode('ascii'), # Supabase bytea via base64 or hex? Usually hex via psql but python client handles base64 for bytea often. Let's use Base64 as standard wrapper
            "nonce": base64.b64encode(nonce).decode('ascii'),
            "owner_name": username,
            "owner_id": user_id,
            "vault_id": vault_id,
            "is_private": 1,
            "updated_at": int(time.time()),
            "integrity_hash": integrity,
            "deleted": 0,
            "synced": 1
        })
        
    print(f"      > Generando 50 Publicos (Cifrados con Vault Key)...")
    for i in range(50):
        svc = f"{random.choice(services)} - {random.randint(1000,9999)}"
        sec_plain = f"Pass_{username}_Team_{i+1}"
        nonce, cipher = encrypt_record_payload(v_key, sec_plain)
        
        integrity = hashlib.sha256(cipher).hexdigest()
        
        batch.append({
            "id": str(uuid.uuid4()),
            "service": svc,
            "username": f"{username.lower()}@team.com",
            "secret": base64.b64encode(cipher).decode('ascii'),
            "nonce": base64.b64encode(nonce).decode('ascii'),
            "owner_name": username,
            "owner_id": user_id,
            "vault_id": vault_id,
            "is_private": 0,
            "updated_at": int(time.time()),
            "integrity_hash": integrity,
            "deleted": 0,
            "synced": 1
        })
        
    return batch

def main():
    print("="*60)
    print(f" REPARACION CRIPTOGRAFICA DE USUARIOS (PASS: {PASS_DEFAULT})")
    print("="*60)
    
    # 1. Limpieza
    print(">>> Purgando 'secrets'...")
    try: sb.table("secrets").delete().neq("id", "0000").execute()
    except: pass

    targets = [
        {"name": "RODOLFO", "vid": "0637ae0d-7446-4c94-bc06-18c918ce596e"}, # ID Real de Rodolfo
        {"name": "KIKI", "vid": str(uuid.uuid4())},
        {"name": "KAREN", "vid": str(uuid.uuid4())},
        {"name": "DANIEL", "vid": str(uuid.uuid4())}
    ]
    
    total = 0
    for t in targets:
        u = t["name"]
        vid = t["vid"]
        
        # 2. Reparar Usuario (Reset Password & Keys)
        pk, vk, uid = ensure_user(u, vid)
        
        # 3. Generar Lote Valido
        records = generate_valid_records(u, uid, vid, pk, vk)
        
        # 4. Insertar
        # Insertamos de a 100
        try:
            sb.table("secrets").insert(records).execute()
            print(f"   [OK] {len(records)} registros insertados para {u}")
            total += len(records)
        except Exception as e:
            print(f"   [ERROR] Fallo insertando {u}: {e}")
            
    print(f"\nDONE. Total: {total}. Recuerda hacer Sync.")
    print(f"NOTA: La contraseña de TODOS estos usuarios ahora es '{PASS_DEFAULT}'")

if __name__ == "__main__":
    main()
