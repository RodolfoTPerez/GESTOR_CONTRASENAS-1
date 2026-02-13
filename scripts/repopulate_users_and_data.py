
import os
import random
import time
import uuid
import base64
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Cargar entorno
load_dotenv()
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

if not URL or not KEY:
    print("❌ Error: Faltan credenciales en .env")
    exit(1)

sb = create_client(URL, KEY)

def get_or_create_users():
    print(">>> Verificando usuarios...")
    res = sb.table("users").select("*").execute()
    users = res.data
    
    # Asegurar 4 usuarios de prueba
    needed = 4 - len(users)
    if needed > 0:
        print(f"!!! Faltan {needed} usuarios. Creando ficticios...")
        for i in range(needed):
            username = f"USER_TEST_{len(users)+i+1}"
            # Vault ID genérico
            v_id = str(uuid.uuid4())
            
            payload = {
                "username": username,
                "role": "user",
                "active": True,
                "vault_id": v_id,
                # Sin password hash real, es solo para poblar datos
                "created_at": datetime.now().isoformat()
            }
            try:
                r = sb.table("users").insert(payload).execute()
                if r.data:
                    users.append(r.data[0])
                    print(f"   + Creado: {username}")
            except Exception as e:
                print(f"   - Error creando {username}: {e}")
    
    # Filtrar solo los primeros 4 para el ejercicio si hay más
    return users[:4]

def purge_all_secrets():
    print("\n>>>  Purgando TODOS los secretos existentes (Limpieza total)...")
    # Borrado masivo (sin where clause tricky, borramos por ID no nulo)
    try:
        sb.table("secrets").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print("   + Tabla 'secrets' limpia.")
    except Exception as e:
        print(f"   ! Error purgando (puede que ya esté vacía): {e}")

def generate_dummy_secret(owner, vault_id):
    services = ["Google", "Facebook", "Twitter", "Amazon", "Netflix", "Spotify", "LinkedIn", "Github", "Slack", "Zoom"]
    svc = random.choice(services)
    
    # Simular encriptación (Fake Base64)
    # Formato: NONCE(12) + CIPHER
    nonce = os.urandom(12)
    cipher = os.urandom(32) 
    secret_blob = base64.b64encode(nonce + cipher).decode('ascii')
    
    return {
        "id": str(uuid.uuid4()),
        "service": f"{svc} - {random.randint(1000,9999)}",
        "username": f"{owner.lower()}@example.com",
        "secret": secret_blob,
        "notes": "Registro generado automáticamente por script de reparación.",
        "owner_name": owner,           # CRÍTICO: VINCULACIÓN POR NOMBRE
        "owner_id": None,              # Opcional, dependiendo de la versión de la DB
        "vault_id": vault_id,          # CRÍTICO: VINCULACIÓN POR BÓVEDA
        "is_private": random.choice([0, 1]),
        "deleted": 0,
        "synced": 1,
        "updated_at": int(time.time())
    }

def populate_data(users):
    print(f"\n>>> Generando 100 registros para cada uno de los {len(users)} usuarios...")
    
    total_created = 0
    for u in users:
        u_name = u["username"]
        v_id = u.get("vault_id")
        
        # Intentar obtener owner_id real
        u_id = u.get("id")
        
        print(f"   => Procesando: {u_name} (Vault: {v_id})")
        
        batch = []
        
        # 1. Generar 50 Privados
        for _ in range(50):
            item = generate_dummy_secret(u_name, v_id)
            item["is_private"] = 1
            if u_id: item["owner_id"] = u_id
            batch.append(item)

        # 2. Generar 50 Publicos
        for _ in range(50):
            item = generate_dummy_secret(u_name, v_id)
            item["is_private"] = 0
            if u_id: item["owner_id"] = u_id
            batch.append(item)
            
        # Insertar en lotes de 100
        try:
            # Quitamos owner_id si falla (fallback dinámico)
            try:
                sb.table("secrets").insert(batch).execute()
            except Exception as e:
                is_col_error = "column" in str(e) and "owner_id" in str(e)
                if is_col_error:
                    print("      ! Columna 'owner_id' no existe. Reintentando solo con 'owner_name'...")
                    for b in batch: b.pop("owner_id", None)
                    sb.table("secrets").insert(batch).execute()
                else:
                    raise e
                    
            print(f"      + 100 generados (50 Priv / 50 Pub) para {u_name}")
            total_created += 100
        except Exception as e:
            print(f"      - Fatality insertando lote: {e}")

    print(f"\n!!! FINALIZADO: {total_created} registros nuevos creados y VINCULADOS CORRECTAMENTE.")

if __name__ == "__main__":
    print("="*60)
    print(" REPARACION DE VINCULACION DE DATOS (4 USUARIOS x 100 REGS)")
    print("="*60)
    
    try:
        users = get_or_create_users()
        if not users:
            print("X No se pudieron obtener usuarios.")
            exit()
            
        print(f"# Usuarios objetivo: {[u['username'] for u in users]}")
        
        purge_all_secrets()
        populate_data(users)
        
    except Exception as e:
        print(f"\n- Error General: {e}")
