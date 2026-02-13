from pathlib import Path
import os
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
import os
import requests
import sqlite3
import base64
from dotenv import load_dotenv

load_dotenv(str(BASE_DIR) + "/.env")
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

def forense_y_limpieza():
    headers = {
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json",
        "x-guardian-user": "RODOLFO"
    }

    print("="*60)
    print("PERITAJE DE DATOS EN LA NUBE")
    print("="*60)

    # 1. Ver qué hay actualmente
    r = requests.get(f"{URL}/rest/v1/users?username=eq.RODOLFO", headers=headers)
    if r.status_code == 200 and r.json():
        u = r.json()[0]
        totp = u.get('totp_secret', '')
        print(f"TOTP actual en Nube: '{totp}' (Longitud: {len(totp)})")
        print(f"Vault ID: {u.get('vault_id')}")
        print(f"Hashes: {u.get('password_hash')[:10]}...")
    else:
        print("No se pudo obtener el perfil de la nube.")
        return

    # 2. LIMPIEZA ATÓMICA
    # Vamos a usar un TOTP de 16 caracteres exactos, sin espacios.
    payload = {
        "totp_secret": "JBSWY3DPEHPK3PXP",
        "active": True
    }
    
    print("\n[Limpieza] Corrigiendo TOTP en Supabase...")
    upd = requests.patch(f"{URL}/rest/v1/users?username=eq.RODOLFO", headers=headers, json=payload)
    print(f"Resultado Update: {upd.status_code}")

    # 3. VERIFICACIÓN POST-LIMPIEZA
    r2 = requests.get(f"{URL}/rest/v1/users?username=eq.RODOLFO", headers=headers)
    u2 = r2.json()[0]
    print(f"TOTP final en Nube: '{u2.get('totp_secret')}' (Longitud: {len(u2.get('totp_secret', ''))})")

    print("\n" + "="*60)
    print("IMPORTANTE: Ahora borra los .db locales UNA VEZ MÁS.")
    print("="*60)

if __name__ == "__main__":
    forense_y_limpieza()
