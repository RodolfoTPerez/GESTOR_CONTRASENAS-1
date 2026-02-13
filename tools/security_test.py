
import requests
import json
from config.config import SUPABASE_URL, SUPABASE_KEY

def run_test():
    url = f"{SUPABASE_URL}/rest/v1/secrets"
    headers_base = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    # VAULT_ID de prueba (sacado del dashboard)
    v_id = "0637ae0d-7446-4c94-bc06-18c918ce596e"

    print("--- INICIANDO PRUEBA DE FUEGO (RLS ELITE) ---")

    # 1. Creamos un registro publico de RODOLFO (Admin)
    payload_rodolfo = {
        "service": "TEST_ADMIN_PUB",
        "username": "ADMIN_USER",
        "secret": "HIDDEN",
        "owner_name": "RODOLFO",
        "is_private": 0,
        "vault_id": v_id
    }
    h_rodolfo = headers_base.copy()
    h_rodolfo.update({"X-Guardian-User": "RODOLFO", "X-Guardian-Vault": v_id})
    
    r1 = requests.post(url, headers=h_rodolfo, json=payload_rodolfo)
    if r1.status_code in (200, 201):
        record_id = r1.json()[0]['id']
        print(f"[OK] Registro de RODOLFO creado (ID: {record_id})")
        
        # 2. INTENTO DE BORRADO POR KIKI (Usuario normal)
        print(f"\n[TEST 1] KIKI intentando borrar registro publico de RODOLFO...")
        h_kiki = headers_base.copy()
        h_kiki.update({"X-Guardian-User": "KIKI", "X-Guardian-Vault": v_id})
        
        r2 = requests.delete(f"{url}?id=eq.{record_id}", headers=h_kiki)
        if r2.status_code == 204 or (r2.status_code == 200 and not r2.json()):
            # En PostgREST, si el RLS bloquea, no da error, solo dice "0 filas afectadas"
            print(f">>> [BLOQUEO EXITOSO] KIKI no pudo borrar el registro (RLS funcionando). Status: {r2.status_code}")
        else:
            print(f"!!! [FALLO] KIKI logro borrar el registro o hubo error: {r2.text}")
    else:
        print(f"Error creando registro de Rodolfo: {r1.text}")
        return

    # 3. Creamos un registro publico de KIKI (Usuario)
    payload_kiki = {
        "service": "TEST_KIKI_PUB",
        "username": "KIKI_USER",
        "secret": "HIDDEN",
        "owner_name": "KIKI",
        "is_private": 0,
        "vault_id": v_id
    }
    r3 = requests.post(url, headers=h_kiki, json=payload_kiki)
    if r3.status_code in (200, 201):
        record_id_kiki = r3.json()[0]['id']
        print(f"\n[OK] Registro de KIKI creado (ID: {record_id_kiki})")
        
        # 4. INTENTO DE BORRADO POR RODOLFO (ADMIN) sobre lo de KIKI
        print(f"[TEST 2] RODOLFO (Admin) intentando borrar registro publico de KIKI...")
        r4 = requests.delete(f"{url}?id=eq.{record_id_kiki}", headers=h_rodolfo)
        # Con Prefer: return=representation, si borra nos devuelve el objeto
        if r4.status_code == 200 and r4.json():
            print(f">>> [ACCESO CONCEDIDO] RODOLFO (Admin) borro con exito el registro de KIKI.")
        else:
            print(f"!!! [FALLO] El Admin no pudo borrar el registro publico: {r4.status_code} {r4.text}")
    
    # Limpieza final (Rodolfo borra su propio test)
    requests.delete(f"{url}?id=eq.{record_id}", headers=h_rodolfo)
    print("\n--- PRUEBA FINALIZADA ---")

if __name__ == "__main__":
    run_test()
