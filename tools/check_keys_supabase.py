import os
import requests
from dotenv import load_dotenv

load_dotenv()
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

def check_keys_nube():
    headers = {
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json"
    }
    
    print("\n" + "="*60)
    print("VERIFICACIÓN DE LLAVES EN SUPABASE")
    print("="*60)
    
    r = requests.get(f"{URL}/rest/v1/users?username=eq.RODOLFO&select=*", headers=headers)
    if r.status_code == 200 and r.json():
        u = r.json()[0]
        print(f"Usuario: {u['username']}")
        print(f"Vault Salt: {'Presente' if u.get('vault_salt') else 'FALTANTE'}")
        print(f"Protected Key (Personal): {'Presente' if u.get('protected_key') else 'FALTANTE'}")
        print(f"Vault ID: {u.get('vault_id')}")
        
        # Check vault_access
        r_acc = requests.get(f"{URL}/rest/v1/vault_access?user_id=eq.{u['id']}", headers=headers)
        if r_acc.status_code == 200 and r_acc.json():
            print(f"Vault Access (Team Key): Presente")
        else:
            print(f"Vault Access (Team Key): FALTANTE")
    else:
        print("No se encontró el perfil.")

if __name__ == "__main__":
    check_keys_nube()
