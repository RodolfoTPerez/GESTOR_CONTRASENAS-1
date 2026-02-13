"""
Verificar invitaciones en Supabase
"""
from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 80)
print("INVITACIONES EN SUPABASE")
print("=" * 80)

invs = supabase.table("invitations").select("*").execute()

if invs.data:
    print(f"\nInvitaciones encontradas: {len(invs.data)}\n")
    for inv in invs.data:
        print(f"Codigo: {inv.get('code')}")
        print(f"  - Rol: {inv.get('role')}")
        print(f"  - Usado: {inv.get('used')}")
        print(f"  - Creado por: {inv.get('created_by', 'N/A')}")
        print(f"  - Vault ID: {inv.get('vault_id', 'N/A')}")
        print(f"  - Wrapped Vault Key: {'SI' if inv.get('wrapped_vault_key') else 'NO'}")
        if inv.get('wrapped_vault_key'):
            print(f"    Length: {len(inv.get('wrapped_vault_key'))} chars")
        print()
else:
    print("\nNo hay invitaciones")

print("=" * 80)
