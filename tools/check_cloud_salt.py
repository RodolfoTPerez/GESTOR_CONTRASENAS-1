
from src.infrastructure.user_manager import UserManager
from src.infrastructure.secrets_manager import SecretsManager
import json

def check_cloud_salt(username):
    print(f"Checking Cloud Status for {username}...")
    sm = SecretsManager() # Global DB initially
    um = UserManager(sm)
    
    # Check directly from Supabase
    try:
        user_res = um.supabase.table("users").select("*").ilike("username", username).execute()
        if user_res.data:
            u = user_res.data[0]
            print(f"User Found: {u['username']}")
            print(f"Vault ID: {u.get('vault_id')}")
            print(f"Vault Salt (Cloud): {u.get('vault_salt')}")
            if not u.get('vault_salt'):
                print("🚨 ALARM: VAULT SALT IS NULL/EMPTY IN CLOUD! This causes Key Rotation on every login.")
            else:
                print("✅ Vault Salt exists in cloud.")
        else:
            print("User not found in Cloud.")
    except Exception as e:
        print(f"Error checking cloud: {e}")

if __name__ == "__main__":
    check_cloud_salt("RODOLFO")
