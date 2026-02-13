"""
Ver datos completos del usuario RODOLFO en Supabase
"""
from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 80)
print("DATOS DE RODOLFO EN SUPABASE")
print("=" * 80)

user = supabase.table("users").select("*").eq("username", "RODOLFO").execute()

if user.data:
    u = user.data[0]
    print("\nCAMPOS:")
    for key, value in u.items():
        value_type = type(value).__name__
        value_len = len(value) if isinstance(value, (str, bytes, list, dict)) else "N/A"
        value_preview = str(value)[:60] if value else "NULL"
        print(f"  {key:20s} | Type: {value_type:10s} | Len: {str(value_len):6s} | Value: {value_preview}")

print("\n" + "=" * 80)
