import sys
import os
import base64
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.infrastructure.remote_storage_client import RemoteStorageClient
from config.config import SUPABASE_URL, SUPABASE_KEY

USERNAME = "RODOLFO"

def check_cloud_hex():
    client = RemoteStorageClient(SUPABASE_URL, SUPABASE_KEY)
    res = client.get_records("users", f"select=id&username=ilike.{USERNAME}")
    if not res: return
    user_id = res[0]['id']
    
    access = client.get_records("vault_access", f"select=*&user_id=eq.{user_id}")
    if not access: return
    
    wmk_raw = access[0]['wrapped_master_key']
    if isinstance(wmk_raw, str):
        # Already hex from supabase probably
        print(f"Cloud Wrapped Key Hex: {wmk_raw[:24]}...")
    else:
        print(f"Cloud Wrapped Key Hex: {wmk_raw.hex()[:24]}...")

if __name__ == "__main__":
    check_cloud_hex()
