from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

try:
    res = supabase.table("invitations").select("*").execute()
    print(f"Datos de invitaciones: {res.data}")
    
    res_u = supabase.table("users").select("username, vault_id, role").execute()
    print(f"Perfiles de usuario: {res_u.data}")
except Exception as e:
    print(f"Error: {e}")
