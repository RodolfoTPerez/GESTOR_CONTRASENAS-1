
import sqlite3
import hashlib
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pathlib import Path

def diagnostic():
    db_path = Path("data/vault_rodolfo.db")
    if not db_path.exists():
        print("No se encontro la DB de Rodolfo.")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("SELECT id, service, secret, nonce, is_private, vault_id FROM secrets WHERE is_private = 0")
    rows = cur.fetchall()
    
    shared_secret_4 = "PASSGUARDIAN_VAULT_4_SHARED_KEY"
    fixed_key_4 = hashlib.pbkdf2_hmac('sha256', shared_secret_4.encode(), b'public_salt', 100000, 32)
    
    print(f"--- Diagnostico de {len(rows)} registros de equipo ---")
    for rid, service, secret, nonce, is_priv, vid in rows:
        success = False
        try:
            aes = AESGCM(fixed_key_4)
            aes.decrypt(nonce, secret, None)
            success = True
            print(f"OK: {service} (ID: {rid}) - Decriptado con LLAVE FIJA TEAM.")
        except:
            pass
            
        if not success:
             print(f"ERROR: {service} (ID: {rid}) - FALLO con llave de equipo. Esta bloqueado con la llave PERSONAL de Rodolfo.")

    conn.close()

if __name__ == "__main__":
    diagnostic()
