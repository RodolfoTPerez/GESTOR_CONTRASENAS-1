"""
Script de emergencia para resetear RODOLFO en SUPABASE
"""
from supabase import create_client
import hashlib
import os
import sys

# Importar configuración
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.config import SUPABASE_URL, SUPABASE_KEY

def hash_password(password, salt):
    dk = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode('utf-8'), 
        salt.encode('utf-8'), 
        100_000
    )
    return dk.hex()

if __name__ == "__main__":
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    username = "RODOLFO"
    new_password = "RODOLFO"
    # Salt fijo para mayor facilidad de restauración
    salt = "4e3f2a1b0c9d8e7f" 
    
    pwd_hash = hash_password(new_password, salt)
    
    print(f"Reseteando {username} en Supabase...")
    
    try:
        # 1. Quitar 2FA y actualizar password hash en Supabase
        res = supabase.table("users").update({
            "password_hash": pwd_hash,
            "salt": salt,
            "totp_secret": None,
            "active": True
        }).eq("username", username.upper()).execute()
        
        print(f"Resultado Supabase: {res.data}")
        print("\n[OK] Usuario RODOLFO reseteado en la NUBE.")
        print("Ahora puedes iniciar sesion con password: RODOLFO y sin 2FA.")
    except Exception as e:
        print(f"Error reseteando en Supabase: {e}")
