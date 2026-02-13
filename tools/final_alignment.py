
import os
import sys
import base64
import sqlite3
from supabase import create_client

# Configuración
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.config import SUPABASE_URL, SUPABASE_KEY
from src.infrastructure.secrets_manager import SecretsManager
from src.infrastructure.user_manager import UserManager
from src.infrastructure.crypto_engine import CryptoEngine

def align_vault():
    print("=== ALINEACIÓN FINAL DE BÓVEDA: RODOLFO & KIKI ===")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 1. RECUPERAR LA LLAVE MAESTRA DESDE RODOLFO
    print(">>> Extrayendo llave maestra de Rodolfo...")
    res_r = supabase.table("users").select("*").eq("username", "RODOLFO").execute()
    prof_r = res_r.data[0]
    salt_r = base64.b64decode(prof_r["vault_salt"])
    
    # Necesitamos el wrapped_master_key de vault_access de Rodolfo
    acc_r = supabase.table("vault_access").select("*").eq("user_id", prof_r['id']).execute()
    wrapped_r = bytes.fromhex(acc_r.data[0]["wrapped_master_key"])
    
    # Des-envolver la llave real
    master_key = CryptoEngine.unwrap_vault_key(wrapped_r, "RODOLFO", salt_r)
    print(f"✅ Llave maestra recuperada ({len(master_key)} bytes)")

    # 2. ENVOLVER LA LLAVE PARA KIKI (Su propio sobre)
    print(">>> Envolviendo llave para KIKI con su propia clave...")
    res_k = supabase.table("users").select("*").eq("username", "KIKI").execute()
    prof_k = res_k.data[0]
    salt_k = base64.b64decode(prof_k["vault_salt"])
    
    wrapped_k = CryptoEngine.wrap_vault_key(master_key, "KIKI1234567890", salt_k)
    
    # 3. ACTUALIZAR NUBE (vault_access de KIKI)
    print(">>> Actualizando vault_access de KIKI en la nube...")
    # Intentar update primero
    upd_k = supabase.table("vault_access").update({"wrapped_master_key": wrapped_k.hex()}).eq("user_id", prof_k['id']).execute()
    if not upd_k.data:
        supabase.table("vault_access").insert({
            "user_id": prof_k['id'], 
            "vault_id": prof_k['vault_id'], 
            "wrapped_master_key": wrapped_k.hex()
        }).execute()

    # 4. ACTUALIZAR PERFIL DE KIKI (SVK)
    # También actualizamos su protected_key para que coincida
    pk_k = CryptoEngine.wrap_vault_key(master_key, "KIKI1234567890", salt_k)
    supabase.table("users").update({"protected_key": base64.b64encode(pk_k).decode('ascii')}).eq("username", "KIKI").execute()

    # 5. SINCRONIZAR LOCAL
    sm = SecretsManager()
    um = UserManager(sm)
    um.sync_user_to_local("KIKI", {**prof_k, "wrapped_vault_key": wrapped_k.hex(), "protected_key": base64.b64encode(pk_k).decode('ascii')})
    
    print("\n✅ ALINEACIÓN COMPLETADA.")
    print("KIKI ya puede abrir el sobre de la bóveda de RODOLFO.")
    print("PRUEBA AHORA: Crea un registro público con KIKI y Rodolfo podrá verlo.")

if __name__ == "__main__":
    align_vault()
