"""
Eliminar usuario KIKI de Supabase y local
"""
from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY
from pathlib import Path
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 80)
print("ELIMINANDO USUARIO KIKI")python check_kiki.py
print("=" * 80)

# 1. Eliminar de users
print("\n[1] Eliminando de tabla 'users'...")
try:
    users = supabase.table("users").select("id").eq("username", "KIKI").execute()
    if users.data:
        for user in users.data:
            supabase.table("users").delete().eq("id", user['id']).execute()
        print(f"   OK - {len(users.data)} registros eliminados")
    else:
        print("   INFO - No se encontro KIKI")
except Exception as e:
    print(f"   ERROR - {e}")

# 2. Eliminar de vault_access
print("\n[2] Eliminando de tabla 'vault_access'...")
try:
    va = supabase.table("vault_access").select("id, user_id").execute()
    if va.data:
        for record in va.data:
            # Verificar si el user_id corresponde a KIKI
            user_check = supabase.table("users").select("username").eq("id", record['user_id']).execute()
            if not user_check.data:  # Si no hay usuario, es KIKI (ya eliminado)
                supabase.table("vault_access").delete().eq("id", record['id']).execute()
                print(f"   OK - Registro huerfano eliminado")
except Exception as e:
    print(f"   WARN - {e}")

# 3. Eliminar DB local
print("\n[3] Eliminando vault_kiki.db...")
vault_db = Path("C:/PassGuardian_v2/data/vault_kiki.db")
if vault_db.exists():
    vault_db.unlink()
    print("   OK - Archivo eliminado")
else:
    print("   INFO - Archivo no existe")

print("\n" + "=" * 80)
print("KIKI ELIMINADA COMPLETAMENTE")
print("=" * 80)
