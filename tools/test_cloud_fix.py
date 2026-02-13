from pathlib import Path
import os
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv(str(BASE_DIR) + "/.env")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

def test_cloud_update():
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
        "x-guardian-user": "RODOLFO" # Usar el bypass que pusimos en RLS
    }
    
    # Intentar traer el perfil de Rodolfo
    print(f"Consultando perfil de RODOLFO en {url}...")
    r = requests.get(f"{url}/rest/v1/users?username=eq.RODOLFO", headers=headers)
    print(f"Status: {r.status_code}")
    if r.status_code == 200 and r.json():
        user = r.json()[0]
        print("Perfil encontrado.")
        # Intentar actualizar el totp_secret a algo limpio
        payload = {"totp_secret": "JBSWY3DPEHPK3PXP"}
        upd = requests.patch(f"{url}/rest/v1/users?username=eq.RODOLFO", headers=headers, json=payload)
        print(f"Update Status: {upd.status_code}")
        print(f"Update Text: {upd.text}")
    else:
        print("No se encontró el perfil o error de acceso.")

if __name__ == "__main__":
    test_cloud_update()
