"""
Verificar datos de KIKI en Supabase
"""
from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 80)
print("DATOS DE KIKI EN SUPABASE")
print("=" * 80)

# 1. Usuario
user = supabase.table("users").select("*").eq("username", "KIKI").execute()

if user.data:
    u = user.data[0]
    print("\n[TABLA USERS]:")
    print(f"  - ID: {u.get('id')}")
    print(f"  - Username: {u.get('username')}")
    print(f"  - Vault ID: {u.get('vault_id')}")
    print(f"  - Protected Key: {'SI' if u.get('protected_key') else 'NO'}")
    if u.get('protected_key'):
        print(f"    Length: {len(u.get('protected_key'))} chars")
    print(f"  - Wrapped Vault Key: {'SI' if u.get('wrapped_vault_key') else 'NO'}")
    print(f"  - Vault Salt: {'SI' if u.get('vault_salt') else 'NO'}")
    
    # 2. Vault Access
    user_id = u.get('id')
    vault_id = u.get('vault_id')
    
    if user_id and vault_id:
        va = supabase.table("vault_access").select("*").eq("user_id", user_id).eq("vault_id", vault_id).execute()
        if va.data:
            print("\n[TABLA VAULT_ACCESS]:")
            v = va.data[0]
            print(f"  - User ID: {v.get('user_id')}")
            print(f"  - Vault ID: {v.get('vault_id')}")
            print(f"  - Wrapped Master Key: {'SI' if v.get('wrapped_master_key') else 'NO'}")
            if v.get('wrapped_master_key'):
                print(f"    Length: {len(v.get('wrapped_master_key'))} chars")
                print(f"    Es HEX: {all(c in '0123456789abcdefABCDEF' for c in v.get('wrapped_master_key'))}")
        else:
            print("\n[TABLA VAULT_ACCESS]: NO ENCONTRADA")
else:
    print("\nKIKI NO EXISTE EN SUPABASE")

print("\n" + "=" * 80)
