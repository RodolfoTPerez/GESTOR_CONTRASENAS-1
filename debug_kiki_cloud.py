
import os
import time
from src.infrastructure.remote_storage_client import RemoteStorageClient
from config.config import SUPABASE_URL, SUPABASE_KEY

client = RemoteStorageClient(SUPABASE_URL, SUPABASE_KEY)
user = "KIKI"
recent_cutoff = int(time.time()) - 3600 # Last hour

print(f"Checking Supabase for {user}...")

# 1. Check user profiles
for user_to_check in ["KIKI", "RODOLFO"]:
    print(f"\n--- Checking {user_to_check} ---")
    users = client.get_records("users", f"select=id,username,vault_id&username=ilike.{user_to_check}")
    if users:
        print(f"User Profile: {users[0]}")
        u_id = users[0]['id']
        v_id = users[0].get('vault_id')
        
        # 2. Check vault access
        if v_id:
            access = client.get_records("vault_access", f"select=*&user_id=eq.{u_id}&vault_id=eq.{v_id}")
            print(f"Vault Access Records for {v_id}: {access}")
        else:
            print("User has no vault_id linked in profile!")
    else:
        print(f"User {user_to_check} not found!")

# 3. Check Kick events
kicks = client.get_records("security_audit", f"select=*&action=eq.KICK&user_name=ilike.KIKI&timestamp=gt.{recent_cutoff}")
print(f"\nRecent KICK events for KIKI: {kicks}")
