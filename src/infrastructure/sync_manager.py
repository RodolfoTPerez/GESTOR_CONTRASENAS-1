import time
import requests
import json
import socket
from pathlib import Path


class SyncManager:
    def __init__(self, secrets_manager, supabase_url, supabase_key):
        self.sm = secrets_manager
        self.supabase_url = supabase_url.rstrip("/")
        self.supabase_key = supabase_key

        self.table = "secrets"

        self.headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json"
        }

    def _has_internet(self):
        try:
            socket.gethostbyname("supabase.co")
            return True
        except socket.gaierror:
            return False

    def backup_to_supabase(self):
        if not self._has_internet():
            raise ConnectionError("No hay conexión a internet.")

        local = self.sm.get_all()
        url = f"{self.supabase_url}/rest/v1/{self.table}"

        requests.delete(url, headers=self.headers)

        payload = []
        for s in local:
            payload.append({
                "id": s["id"],
                "service": s["service"],
                "username": s["username"],
                "secret": s["secret"],
                "notes": s.get("notes", None),
                "updated_at": int(time.time())
            })

        if payload:
            headers = self.headers.copy()
            headers["Prefer"] = "resolution=merge-duplicates"

            r = requests.post(url, headers=headers, data=json.dumps(payload))
            if r.status_code not in (200, 201):
                raise Exception(f"Error en backup: {r.text}")

    def restore_from_supabase(self):
        if not self._has_internet():
            raise ConnectionError("No hay conexión a internet.")

        url = f"{self.supabase_url}/rest/v1/{self.table}?select=*"
        r = requests.get(url, headers=self.headers)

        if r.status_code != 200:
            raise Exception(f"Error al restaurar: {r.text}")

        remote = r.json()

        self._clear_local()

        for s in remote:
            self.sm.add_secret(
                s.get("service"),
                s.get("username"),
                s.get("secret"),
                s.get("notes")
            )

    def sync(self):
        if not self._has_internet():
            raise ConnectionError("No hay conexión a internet.")

        local = self.sm.get_all()
        url = f"{self.supabase_url}/rest/v1/{self.table}?select=*"
        r = requests.get(url, headers=self.headers)

        if r.status_code != 200:
            raise Exception(f"Error al sincronizar: {r.text}")

        remote = r.json()

        local_map = {s["id"]: s for s in local}
        remote_map = {s["id"]: s for s in remote if s.get("id") is not None}

        for lid, lrec in local_map.items():
            rrec = remote_map.get(lid)
            if rrec is None or self._record_changed(lrec, rrec):
                self._upload_record(lrec)

        for rid, rrec in remote_map.items():
            if rid not in local_map:
                self.sm.add_secret(
                    rrec["service"],
                    rrec["username"],
                    rrec["secret"],
                    rrec.get("notes")
                )

    def _clear_local(self):
        self.sm.conn.execute("DELETE FROM secrets")
        self.sm.conn.commit()

    def _upload_record(self, rec):
        url = f"{self.supabase_url}/rest/v1/{self.table}"

        payload = {
            "id": rec["id"],
            "service": rec["service"],
            "username": rec["username"],
            "secret": rec["secret"],
            "notes": rec.get("notes"),
            "updated_at": int(time.time())
        }

        headers = self.headers.copy()
        headers["Prefer"] = "resolution=merge-duplicates"

        r = requests.post(url, headers=headers, data=json.dumps(payload))
        if r.status_code not in (200, 201):
            raise Exception(f"Error subiendo registro: {r.text}")

    def _record_changed(self, local, remote):
        fields = ["service", "username", "secret", "notes"]
        for f in fields:
            if (local.get(f) or "") != (remote.get(f) or ""):
                return True
        return False
