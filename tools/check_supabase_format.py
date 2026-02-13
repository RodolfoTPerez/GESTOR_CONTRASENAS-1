from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
response = supabase.table("users").select("protected_key, wrapped_vault_key, vault_salt").eq("username", "RODOLFO").execute()

if response.data:
    pk = response.data[0].get('protected_key')
    wvk = response.data[0].get('wrapped_vault_key')
    vs = response.data[0].get('vault_salt')
    
    print("=" * 80)
    print("FORMATO REAL DE LLAVES EN SUPABASE")
    print("=" * 80)
    
    print(f"\n[1] PROTECTED KEY:")
    print(f"    Type: {type(pk)}")
    print(f"    Length: {len(pk) if pk else 0}")
    print(f"    First 100 chars: {str(pk)[:100]}")
    print(f"    Repr: {repr(pk)[:100]}")
    
    print(f"\n[2] WRAPPED VAULT KEY:")
    print(f"    Type: {type(wvk)}")
    print(f"    Length: {len(wvk) if wvk else 0}")
    print(f"    First 100 chars: {str(wvk)[:100]}")
    print(f"    Repr: {repr(wvk)[:100]}")
    
    print(f"\n[3] VAULT SALT:")
    print(f"    Type: {type(vs)}")
    print(f"    Length: {len(vs) if vs else 0}")
    print(f"    First 100 chars: {str(vs)[:100]}")
    print(f"    Repr: {repr(vs)[:100]}")
    
    print("\n" + "=" * 80)
else:
    print("No se encontro el usuario RODOLFO")
