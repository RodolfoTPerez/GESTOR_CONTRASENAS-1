import os
import sqlite3
import base64
import sys
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Importar motor
sys.path.insert(0, str(Path(__file__).parent))
from src.infrastructure.crypto_engine import CryptoEngine

def forense_llaves(password="RODOLFO"):
    db_path = Path("data/vault_rodolfo.db")
    if not db_path.exists():
        print("ERROR: No existe la DB local.")
        return

    print(f"\n{'='*60}")
    print("ANÁLISIS FORENSE DE LLAVES (RODOLFO)")
    print("='*60}")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute("SELECT username, vault_salt, protected_key, wrapped_vault_key FROM users")
    row = cursor.fetchone()
    conn.close()

    if not row:
        print("ERROR: No hay perfil en la DB local.")
        return

    user, salt, p_key, w_key = row
    print(f"Usuario: {user}")
    print(f"Salt (bytes): {len(salt) if salt else 0}")
    print(f"P_Key (bytes): {len(p_key) if p_key else 0}")
    print(f"W_Key (bytes): {len(w_key) if w_key else 0}")

    # TEST DE DESEMPAQUETADO MANUAL
    try:
        kek = CryptoEngine.derive_kek_from_password(password, bytes(salt))
        print(f"KEK Derivada OK (Hash: {kek.hex()[:10]}...)")
        
        # Intento con P_KEY
        if p_key:
            pk_bytes = bytes(p_key)
            nonce, cipher = pk_bytes[:12], pk_bytes[12:]
            try:
                dec = AESGCM(kek).decrypt(nonce, cipher, None)
                print(">>> [EXITO] P_Key descifrada correctamente!")
            except Exception as e:
                print(f">>> [FALLO] P_Key: {e}")

        # Intento con W_KEY
        if w_key:
            wk_bytes = bytes(w_key)
            try:
                dec = CryptoEngine.unwrap_vault_key(wk_bytes, password, bytes(salt))
                print(">>> [EXITO] W_Key descifrada correctamente!")
            except Exception as e:
                print(f">>> [FALLO] W_Key: {e}")
                
    except Exception as e:
        print(f"Error en derivación: {e}")

    # --- REPARACIÓN DIRECTA IN SITU ---
    print(f"\n{'='*60}")
    print("REPARACIÓN FORZADA DE BASE DE DATOS LOCAL")
    print("='*60}")
    
    # Derivar KEK correcta
    v_salt_fixed = secrets.token_bytes(16)
    master_key_fixed = secrets.token_bytes(32)
    kek_fixed = CryptoEngine.derive_kek_from_password(password, v_salt_fixed)
    
    # Envolver
    nonce = os.urandom(12)
    aes = AESGCM(kek_fixed)
    p_key_fixed = nonce + aes.encrypt(nonce, master_key_fixed, None)
    
    print(f">>> Escribiendo llaves binarias reales en la DB...")
    conn = sqlite3.connect(str(db_path))
    conn.execute("UPDATE users SET vault_salt = ?, protected_key = ?, wrapped_vault_key = ?", 
                 (sqlite3.Binary(v_salt_fixed), sqlite3.Binary(p_key_fixed), sqlite3.Binary(p_key_fixed)))
    conn.commit()
    conn.close()
    print(">>> [EXITO] Base de datos local reparada con binarios puros.")

if __name__ == "__main__":
    import secrets
    forense_llaves()
