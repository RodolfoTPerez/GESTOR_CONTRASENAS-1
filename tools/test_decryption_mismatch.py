from pathlib import Path
import os
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
import sqlite3
import os
import sys
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Configuración de rutas
sys.path.insert(0, os.path.abspath(str(BASE_DIR) + ""))
from src.infrastructure.secrets_manager import SecretsManager

def check_decryption():
    sm = SecretsManager()
    # Loguear como RODOLFO
    # Usamos el password RODOLFO que vimos en el script de reparación
    sm.set_active_user("RODOLFO", "RODOLFO")
    
    if not sm.master_key:
        print("Error: No se pudo cargar la llave maestra para RODOLFO.")
        return

    db_path = "data/vault_rodolfo.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT id, service, secret, nonce, owner_name, is_private FROM secrets WHERE id IN (108, 109)")
    
    keys = [sm.personal_key, sm.vault_key, sm.master_key]
    
    for row in cursor:
        rid, svc, enc_data, nonce, owner, is_priv = row
        print(f"\nChecking Record {rid}: {svc} (Owner: {owner}, Private: {is_priv})")
        
        decrypted = False
        for i, k in enumerate(keys):
            if not k: continue
            try:
                aes = AESGCM(k)
                dec = aes.decrypt(nonce, enc_data, None)
                print(f"  [SUCCESS] Decrypted with key index {i}!")
                print(f"  Result: {dec.decode('utf-8')}")
                decrypted = True
                break
            except Exception as e:
                pass
        
        if not decrypted:
            print("  [FAIL] Could not decrypt with any of Rodolfo's keys.")

    conn.close()

if __name__ == "__main__":
    check_decryption()
