import os
import sys
from postgrest import APIError

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client

def fix_orphans():
    print(">>> INICIANDO OPERACION RESCATE DE HUERFANOS...")
    
    # 1. Conectar a Supabase
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(">>> Conexión a Nube establecida.")
    except Exception as e:
        print(f"!!! Error conectando a Supabase: {e}")
        return

    # 2. Identificar al Admin (Asumimos RODOLFO o pedimos input)
    # Buscamos u admin activo
    res = supabase.table("users").select("username, vault_id").eq("role", "admin").execute()
    if not res.data:
        print("!!! No se encontraron administradores para adoptar los secretos.")
        return
    
    # Usamos el primer admin encontrado (RODOLFO normalmente)
    admin_user = res.data[0]
    admin_name = admin_user["username"]
    correct_vault_id = admin_user["vault_id"]
    
    if not correct_vault_id:
        print(f"!!! El administrador {admin_name} no tiene un vault_id válido. No se puede proceder.")
        return
        
    print(f">>> Administrador de destino: {admin_name} (Vault ID: {correct_vault_id})")

    # 3. Buscar Huérfanos (Secretos del Admin pero sin Vault ID)
    # También buscamos secretos que tengan owner_name = admin_name pero vault_id IS NULL
    orphans_res = supabase.table("secrets").select("id, service").eq("owner_name", admin_name).is_("vault_id", "null").execute()
    orphans = orphans_res.data
    
    if not orphans:
        print(">>> ¡Buenas noticias! No se encontraron secretos huérfanos (con vault_id NULL) para este administrador.")
        return

    print(f">>> Se encontraron {len(orphans)} secretos huérfanos:")
    for o in orphans:
        print(f"    - {o.get('service', '???')} (ID: {o['id']})")

    # 4. Solución
    print("\n>>> Aplicando corrección masiva...")
    try:
        update_res = supabase.table("secrets").update({"vault_id": correct_vault_id}).eq("owner_name", admin_name).is_("vault_id", "null").execute()
        # La API de supabase-py a veces devuelve datos en .data, a veces en el return directo dependiendo de la versión
        # Asumimos éxito si no hay excepción.
        
        print(f">>> ¡ÉXITO! Se han actualizado los registros.")
        print(f">>> Ahora pertenecen legalmente a la bóveda {correct_vault_id}.")
        print(">>> Por favor, reinicia tu aplicación o dale a 'Sincronizar' para verlos.")
        
    except APIError as e:
        print(f"!!! Error al actualizar: {e}")
    except Exception as e:
        print(f"!!! Error inesperado: {e}")

if __name__ == "__main__":
    fix_orphans()
