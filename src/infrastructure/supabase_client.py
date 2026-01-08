import os
from supabase import create_client
from .crypto_utils import encrypt, decrypt

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class SupabaseClient:
    def __init__(self):
        self.client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def count_secrets(self):
        return self.client.table("secrets").select("*", count="exact").execute().count

    def sync_secrets(self, secrets_list: list):
        for s in secrets_list:
            record = {
                "service": s["service"],
                "user": s["user"],
                "secret": s["secret"],
                "nonce": s["nonce"],
                "deleted": s.get("deleted", 0)
            }
            # Upsert para evitar duplicados
            self.client.table("secrets").upsert(record, on_conflict=["service"]).execute()

