"""
Verificar estado de Supabase
"""
from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 80)
print("VERIFICANDO ESTADO DE SUPABASE")
print("=" * 80)

# Verificar users
print("\n[1] Tabla 'users':")
try:
    users = supabase.table("users").select("username, id").execute()
    if users.data:
        print(f"   Usuarios encontrados: {len(users.data)}")
        for user in users.data:
            print(f"   - {user['username']} (ID: {user['id']})")
    else:
        print("   [OK] Tabla vacia")
except Exception as e:
    print(f"   [ERROR] {e}")

# Verificar vault_access
print("\n[2] Tabla 'vault_access':")
try:
    va = supabase.table("vault_access").select("*").execute()
    if va.data:
        print(f"   Registros encontrados: {len(va.data)}")
    else:
        print("   [OK] Tabla vacia")
except Exception as e:
    print(f"   [ERROR] {e}")

# Verificar secrets
print("\n[3] Tabla 'secrets':")
try:
    secrets = supabase.table("secrets").select("id").execute()
    if secrets.data:
        print(f"   Registros encontrados: {len(secrets.data)}")
    else:
        print("   [OK] Tabla vacia")
except Exception as e:
    print(f"   [ERROR] {e}")

print("\n" + "=" * 80)
