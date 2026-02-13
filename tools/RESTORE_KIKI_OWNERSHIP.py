import sqlite3
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

db_path = "data/vault_rodolfo.db"
if not os.path.exists(db_path):
    print("Error: DB not found")
else:
    conn = sqlite3.connect(db_path)
    
    # Mapeo de IDs que alteré erróneamente
    # Usamos los servicios para estar seguros
    revert_list = [
        {"svc": "KIKI 1", "cid": "2509e41a-5390-45f7-a846-1d8b8362750f"},
        {"svc": "KIKI 2", "cid": "ba692b44-b533-4e55-b8a6-08cf10fd167b"},
        {"svc": "KIKI 4", "cid": "0fdd62f4-f606-46e8-8e85-a5d92c92f99f"},
        {"svc": "RODOLFO 3", "cid": "2c69f8a6-2120-4784-afd7-262472d7378f"},
        {"svc": "KIKI 3", "cid": None}
    ]

    print(">>> Iniciando DEVOLUCIÓN de propiedad a KIKI...")
    for item in revert_list:
        svc = item["svc"]
        cid = item["cid"]
        
        # 1. Revertir Local
        conn.execute("UPDATE secrets SET owner_name = 'KIKI', synced = 1 WHERE service = ?", (svc,))
        print(f"  [Local] Propiedad de '{svc}' devuelta a KIKI.")
        
        # 2. Revertir Nube (Si tenemos el ID)
        if cid:
            try:
                supabase.table("secrets").update({"owner_name": "KIKI"}).eq("id", cid).execute()
                print(f"    [Cloud] Propiedad de '{svc}' devuelta a KIKI en Supabase.")
            except Exception as e:
                print(f"    [Cloud Error] No se pudo actualizar {svc}: {e}")

    conn.commit()
    conn.close()
    print(">>> Restauración de propiedad finalizada.")
