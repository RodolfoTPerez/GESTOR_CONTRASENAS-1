from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

print("--- AUDITORÍA DE SECRETS EN SUPABASE ---")
res = supabase.table("secrets").select("id, service, owner_name, is_private, vault_id").execute()
for r in res.data:
    print(f"Record: {r['service']} | Owner: {r['owner_name']} | Private: {r['is_private']} | Vault: {r['vault_id']}")

print("\n--- PERFILES DE USUARIOS ---")
res_u = supabase.table("users").select("username, vault_id").execute()
for u in res_u.data:
    print(f"User: {u['username']} | Vault: {u['vault_id']}")
