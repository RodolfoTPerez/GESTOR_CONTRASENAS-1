
import os
import sys
import base64
import hashlib
import sqlite3
from supabase import create_client

# Configuración
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.config import SUPABASE_URL, SUPABASE_KEY
from src.infrastructure.crypto_engine import CryptoEngine

def force_alignment_v3():
    print("="*60)
    print("   STRICT ALIGNMENT V3 - CROSS-USER PROTOCOL")
    print("="*60)
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 1. Recuperar la Llave Maestra Real de RODOLFO
    print("[*] Accessing Rodolfo's Master Key...")
    res_r = supabase.table("users").select("id, vault_salt, vault_id").eq("username", "RODOLFO").execute()
    u_id_r = res_r.data[0]['id']
    v_id = res_r.data[0]['vault_id']
    salt_r = base64.b64decode(res_r.data[0]["vault_salt"])
    
    acc_r = supabase.table("vault_access").select("wrapped_master_key").eq("user_id", u_id_r).eq("vault_id", v_id).execute()
    wrapped_r = bytes.fromhex(acc_r.data[0]["wrapped_master_key"])
    
    # Des-envolver la llave maestra
    master_key = CryptoEngine.unwrap_vault_key(wrapped_r, "RODOLFO", salt_r)
    mk_hash = hashlib.sha256(master_key).hexdigest()
    print(f"[*] PARITY MASTER KEY: {mk_hash[:16]}... [LOCKED]")

    # 2. Alinear a KIKI (Paridad bit a bit para su password)
    KIKI_PWD = "KIKI1234567890"
    print(f"[*] Re-wrapping for KIKI...")
    res_k = supabase.table("users").select("id, vault_salt").eq("username", "KIKI").execute()
    u_id_k = res_k.data[0]['id']
    salt_k = base64.b64decode(res_k.data[0]["vault_salt"])
    
    # Nueva encriptación para Kiki usando SU password de 14 caracteres
    new_wrapped_k = CryptoEngine.wrap_vault_key(master_key, KIKI_PWD, salt_k)
    
    # 3. ACTUALIZACIÓN EN NUBE (Estructura Correcta)
    # A. En vault_access (Donde el UserManager la descarga)
    supabase.table("vault_access").update({"wrapped_master_key": new_wrapped_k.hex()}).eq("user_id", u_id_k).eq("vault_id", v_id).execute()
    # B. En users.protected_key (Copia de respaldo personal)
    supabase.table("users").update({"protected_key": base64.b64encode(new_wrapped_k).decode('ascii')}).eq("username", "KIKI").execute()
    print("[*] Cloud sync completed (vault_access + user_profile).")

    # 4. FORZADO EN BASE DE DATOS LOCAL (Bypass de Cache)
    db_kiki = "data/vault_kiki.db"
    if os.path.exists(db_kiki):
        conn = sqlite3.connect(db_kiki)
        # Actualizamos ambas columnas para asegurar que el SecretsManager la encuentre no importa el método
        conn.execute("UPDATE users SET protected_key = ?, wrapped_vault_key = ?, vault_id = ? WHERE UPPER(username) = 'KIKI'", 
                    (sqlite3.Binary(new_wrapped_k), sqlite3.Binary(new_wrapped_k), v_id))
        conn.commit()
        conn.close()
        print(f"[*] Local vault '{db_kiki}' patch applied.")

    print("\n" + "="*60)
    print("ALINEACIÓN EXITOSA: La barrera criptográfica ha sido eliminada.")
    print("IMPORTANTE: Reinicia la App. Los nuevos registros serán 100% legibles.")
    print("="*60)

if __name__ == "__main__":
    force_alignment_v3()
