import requests
import json
import logging
import base64
import time

logger = logging.getLogger(__name__)

class RemoteStorageClient:
    """Cliente para intercomunicación con el nodo central (Supabase)."""
    
    def __init__(self, supabase_url, supabase_key):
        self.supabase_url = supabase_url.rstrip("/")
        self.supabase_key = supabase_key
        self.session = requests.Session()
        self.headers = {}
        self._refresh_identity_headers(None, None, None, "user")

    def _refresh_identity_headers(self, user, u_id, v_id, role):
        self.headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            "x-guardian-user": str(user or "").upper(),
            "x-guardian-user-id": str(u_id or "00000000-0000-0000-0000-000000000000"),
            "x-guardian-vault": str(v_id or "00000000-0000-0000-0000-000000000000"),
            "x-guardian-role": str(role or "user").lower(),
        }
        self.session.headers.update(self.headers)

    def check_internet(self):
        try:
            requests.head(self.supabase_url, timeout=2.0)
            return True
        except:
            return False

    def check_supabase(self, table):
        try:
            url = f"{self.supabase_url}/rest/v1/{table}?select=id&limit=1"
            r = self.session.get(url, timeout=3)
            return r.status_code in (200, 204)
        except:
            return False

    def post_records(self, table, payload, merge_duplicates=True):
        url = f"{self.supabase_url}/rest/v1/{table}"
        headers = self.headers.copy()
        if merge_duplicates:
            headers["Prefer"] = "resolution=merge-duplicates"
        
        r = self.session.post(url, headers=headers, data=json.dumps(payload))
        if r.status_code not in (200, 201, 204):
            raise Exception(f"HTTP {r.status_code}: {r.text}")
        return r

    def get_records(self, table, params="select=*"):
        url = f"{self.supabase_url}/rest/v1/{table}?{params}"
        r = self.session.get(url)
        if r.status_code != 200:
            raise Exception(f"HTTP {r.status_code}: {r.text}")
        return r.json()

    def delete_record(self, table, record_id):
        url = f"{self.supabase_url}/rest/v1/{table}?id=eq.{record_id}"
        r = self.session.delete(url)
        if r.status_code not in (200, 204):
            logger.error(f"Error deleting record {record_id}: {r.text}")
        return r

    def get_public_ip(self):
        try:
            return self.session.get("https://api.ipify.org", timeout=3).text
        except:
            return "Unknown"
