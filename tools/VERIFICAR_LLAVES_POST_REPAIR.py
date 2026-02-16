import os
import sys
import base64
import hashlib
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def verificar_estado():
    print("\n" + "="*60)
    print("VERIFICACIÓN POST-REPARACIÓN NUCLEAR")
    print("="*60)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 1. Obtener datos de RODOLFO
    res = supabase.table("users").select("*").eq("username", "RODOLFO").execute()
    if not res.data:
        print("ERROR: No se encontró al usuario RODOLFO.")
        return
    
    user_data = res.data[0]
    print(f"\n1. DATOS DEL USUARIO:")
    print(f"   ID: {user_data['id']}")
    print(f"   Vault ID: {user_data['vault_id']}")
    print(f"   Password Hash: {user_data['password_hash'][:20]}...")
    print(f"   Salt: {user_data['salt']}")
    
    # 2. Verificar password
    import getpass
    password = getpass.getpass("Ingrese contraseña para VERIFICACIÓN: ")
    salt = user_data['salt']
    stored_hash = user_data['password_hash']
    
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    computed_hash = dk.hex()
    
    password_ok = (computed_hash == stored_hash)
    print(f"\n2. VERIFICACIÓN DE PASSWORD:")
    print(f"   Password 'RODOLFO' coincide: {'SI' if password_ok else 'NO'}")
    
    # 3. Verificar llaves
    vault_salt_b64 = user_data.get('vault_salt')
    protected_key_b64 = user_data.get('protected_key')
    
    print(f"\n3. LLAVES GUARDADAS:")
    print(f"   vault_salt existe: {'SI' if vault_salt_b64 else 'NO'}")
    print(f"   protected_key existe: {'SI' if protected_key_b64 else 'NO'}")
    
    if vault_salt_b64:
        # Handle bytea hex format (\x...)
        if isinstance(vault_salt_b64, str) and vault_salt_b64.startswith("\\x"):
            vault_salt = bytes.fromhex(vault_salt_b64[2:])
        else:
            vault_salt = base64.b64decode(vault_salt_b64)
        print(f"   vault_salt longitud: {len(vault_salt)} bytes")
    
    if protected_key_b64:
        # Handle bytea hex format (\x...)
        if isinstance(protected_key_b64, str) and protected_key_b64.startswith("\\x"):
            protected_key = bytes.fromhex(protected_key_b64[2:])
        else:
            protected_key = base64.b64decode(protected_key_b64)
        print(f"   protected_key longitud: {len(protected_key)} bytes")
    
    # 4. Verificar vault_access
    user_id = user_data['id']
    vault_id = user_data['vault_id']
    
    va_res = supabase.table("vault_access").select("*").eq("user_id", user_id).eq("vault_id", vault_id).execute()
    
    print(f"\n4. VAULT_ACCESS:")
    if va_res.data:
        wrapped_key = va_res.data[0].get('wrapped_master_key')
        print(f"   wrapped_master_key existe: {'SI' if wrapped_key else 'NO'}")
        if wrapped_key:
            print(f"   wrapped_master_key longitud: {len(wrapped_key)} caracteres")
    else:
        print(f"   NO hay registro en vault_access")
    
    # 5. Intentar descifrar la protected_key
    if vault_salt_b64 and protected_key_b64 and password_ok:
        print(f"\n5. PRUEBA DE DESCIFRADO:")
        try:
            from src.infrastructure.crypto_engine import CryptoEngine
            
            # Decode vault_salt
            if isinstance(vault_salt_b64, str) and vault_salt_b64.startswith("\\x"):
                vault_salt = bytes.fromhex(vault_salt_b64[2:])
            else:
                vault_salt = base64.b64decode(vault_salt_b64)
            
            # Decode protected_key
            if isinstance(protected_key_b64, str) and protected_key_b64.startswith("\\x"):
                protected_key = bytes.fromhex(protected_key_b64[2:])
            else:
                protected_key = base64.b64decode(protected_key_b64)
            
            master_key = CryptoEngine.unwrap_vault_key(protected_key, password, vault_salt)
            print(f"   DESCIFRADO EXITOSO")
            print(f"   Master Key longitud: {len(master_key)} bytes")
        except Exception as e:
            print(f"   FALLO AL DESCIFRAR: {e}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    verificar_estado()
