import time
import json
import base64
import logging
from src.infrastructure.remote_storage_client import RemoteStorageClient

logger = logging.getLogger(__name__)

class SyncManager:
    def __init__(self, secrets_manager, supabase_url, supabase_key):
        self.sm = secrets_manager
        self.client = RemoteStorageClient(supabase_url, supabase_key)
        self.table = "secrets"
        self.audit_table = "security_audit"
        self._refresh_identity_headers()

    def _refresh_identity_headers(self):
        user = self.sm.current_user
        u_id = self.sm.current_user_id
        v_id = self.sm.current_vault_id
        role = getattr(self.sm, "user_role", "user")
        self.client._refresh_identity_headers(user, u_id, v_id, role)

    def check_internet(self):
        return self.client.check_internet()

    def check_supabase(self):
        return self.client.check_supabase(self.table)

    def _encode_secret(self, nonce_bytes, secret_bytes):
        combined = nonce_bytes + secret_bytes
        return base64.b64encode(combined).decode('ascii')

    def _decode_secret(self, encoded_str):
        if ":" in encoded_str:
            parts = encoded_str.split(":")
            nonce = base64.b64decode(parts[0])
            cipher = base64.b64decode(parts[1])
            return nonce, cipher
        data = base64.b64decode(encoded_str)
        return data[:12], data[12:]

    def backup_to_supabase(self, progress_callback=None):
        if not self.check_internet():
            raise ConnectionError("No internet connection.")

        local = self.sm.get_all_encrypted()
        if not local: raise Exception("No local data to backup.")

        if progress_callback: progress_callback(0, "Initializing backup...")
        total = len(local)
        payload = []
        for i, s in enumerate(local):
            if progress_callback:
                progress_callback(10 + int((i / total) * 70), f"Encoding: {s['service']}")
            
            c_id = s.get("cloud_id") or self._ensure_cloud_id(s)
            item = {
                "id": c_id,
                "service": s["service"],
                "username": s["username"],
                "secret": self._encode_secret(s["nonce_blob"], s["secret_blob"]),
                "notes": s.get("notes"),
                "updated_at": int(time.time()),
                "deleted": s.get("deleted", 0),
                "owner_name": s.get("owner_name"),
                "owner_id": self.sm.current_user_id,
                "is_private": s.get("is_private", 0),
                "synced": 1,
                "vault_id": s.get("vault_id") or self.sm.current_vault_id
            }
            payload.append(item)

        if payload:
            if progress_callback: progress_callback(90, "Uploading data...")
            self.client.post_records(self.table, payload)
        
        if progress_callback: progress_callback(100, "Backup complete.")
        self.sync_audit_logs()

    def _ensure_cloud_id(self, record):
        import uuid
        c_id = str(uuid.uuid4())
        self.sm.conn.execute("UPDATE secrets SET cloud_id=? WHERE id=?", (c_id, record["id"]))
        self.sm.conn.commit()
        return c_id

    def delete_from_supabase(self, sid):
        row = self.sm.conn.execute("SELECT cloud_id, owner_name FROM secrets WHERE id = ?", (sid,)).fetchone()
        if not row: return
        c_id = row[0] or f"{row[1]}_{sid}"
        self.client.delete_record(self.table, c_id)

    def restore_from_supabase(self, progress_callback=None):
        if not self.check_internet(): raise ConnectionError("No internet.")
        remote = self.client.get_records(self.table)
        if not remote: raise Exception("Remote node is empty.")

        if progress_callback: progress_callback(10, "Preparing local storage...")
        total = len(remote)
        self.sm.conn.execute("BEGIN TRANSACTION")
        self.sm.conn.execute("DELETE FROM secrets")
        for i, s in enumerate(remote):
            if progress_callback and i % 5 == 0:
                progress_callback(20 + int((i/total)*80), f"Restoring: {s.get('service')}")
            nonce, cipher = self._decode_secret(s.get("secret", ""))
            params = (
                s["service"], s["username"], cipher, nonce, int(time.time()),
                1 if str(s.get("deleted")).lower() in ("1", "true", "t") else 0,
                "restored", s.get("notes"), s.get("owner_name") or self.sm.current_user,
                1, 1 if str(s.get("is_private")).lower() in ("1", "true", "t") else 0,
                s.get("vault_id"), s.get("id")
            )
            self.sm.conn.execute("""
                INSERT OR REPLACE INTO secrets 
                (service, username, secret, nonce, updated_at, deleted, integrity_hash, notes, owner_name, synced, is_private, vault_id, cloud_id) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, params)
        self.sm.conn.commit()
        if progress_callback: progress_callback(100, "Restore complete.")

    def sync(self, progress_callback=None, cloud_user_id=None):
        if not self.check_internet(): raise ConnectionError("No internet.")
        self._refresh_identity_headers()
        self._sync_shared_keys(cloud_user_id)
        self.sm.refresh_vault_context()

        if progress_callback: progress_callback(5, "Checking for changes...")
        downloaded = self._pull_cloud_to_local()
        local_mine = self.sm.get_all_encrypted(only_mine=True)
        has_local_changes = any(not r.get("synced") or r.get("deleted") for r in local_mine)

        uploaded = {"success": 0, "failed": 0}
        if has_local_changes:
            if progress_callback: progress_callback(30, "Uploading local changes...")
            uploaded = self._push_local_to_cloud()
        
        self.sync_audit_logs()
        if progress_callback: progress_callback(100, f"Sync finished. ↑{uploaded['success']} ↓{downloaded}")
        return {"uploaded": uploaded["success"], "downloaded": downloaded, "errors": uploaded["failed"]}

    def _sync_shared_keys(self, cloud_user_id=None):
        try:
            u_id = cloud_user_id
            if not u_id:
                res = self.client.get_records("users", f"select=id&username=ilike.{self.sm.current_user}")
                if res: u_id = res[0]['id']
            if not u_id: return
            accesses = self.client.get_records("vault_access", f"select=*&user_id=eq.{u_id}")
            for acc in accesses:
                v_id = acc.get("vault_id")
                w_key = acc.get("wrapped_master_key")
                if v_id and w_key:
                    logger.info(f"[Sync] Persisting access to vault {v_id}")
                    self.sm.save_vault_access_local(v_id, bytes.fromhex(w_key) if isinstance(w_key, str) else w_key, synced=1)
        except Exception as e: logger.error(f"Error syncing keys: {e}")

    def _push_local_to_cloud(self):
        stats = {"success": 0, "failed": 0}
        for rec in self.sm.get_all_encrypted(only_mine=True):
            if rec.get("synced"): continue
            try:
                if self._upload_record(rec):
                    self.sm.mark_as_synced(rec["id"], 1)
                    stats["success"] += 1
            except: stats["failed"] += 1
        return stats

    def _pull_cloud_to_local(self):
        user = (self.sm.current_user or "").upper()
        if not user:
            logger.warning("[Sync] Skip pull: No active user context.")
            return 0
        remote = self.client.get_records(self.table, f"select=*&or=(is_private.eq.0,owner_name.eq.{user})")
        local_raw = self.sm.get_all_encrypted()
        local_cloud_ids = {s.get("cloud_id") for s in local_raw if s.get("cloud_id")}
        count = 0
        for rr in remote:
            if rr["id"] in local_cloud_ids: continue
            nonce, cipher = self._decode_secret(rr["secret"])
            self.sm.add_secret_encrypted(
                service=rr["service"],
                username=rr["username"],
                secret_blob=cipher,
                nonce_blob=nonce,
                integrity="",
                notes=rr.get("notes"),
                is_private=1 if str(rr.get("is_private")).lower() in ("1", "true", "t") else 0,
                owner_name=rr.get("owner_name"),
                vault_id=rr.get("vault_id"),
                deleted=rr.get("deleted", 0),
                synced=1,
                cloud_id=rr["id"]
            )
            count += 1
        return count

    def _upload_record(self, rec):
        c_id = rec.get("cloud_id") or self._ensure_cloud_id(rec)
        payload = {
            "id": c_id, "service": rec["service"], "username": rec["username"],
            "secret": self._encode_secret(rec["nonce_blob"], rec["secret_blob"]),
            "notes": rec.get("notes"), "updated_at": int(time.time()),
            "owner_name": str(rec.get("owner_name") or self.sm.current_user or "unknown").upper(),
            "is_private": rec.get("is_private", 0), "deleted": rec.get("deleted", 0),
            "vault_id": rec.get("vault_id") or self.sm.current_vault_id
        }
        self.client.post_records(self.table, [payload])
        return True

    def sync_single_record(self, record_id):
        if not self.check_internet(): return
        row = self.sm.conn.execute("SELECT * FROM secrets WHERE id=?", (record_id,)).fetchone()
        if row: self._upload_record(self._row_to_dict(row))

    def _row_to_dict(self, row):
        """
        Mapeo robusto de row (tuple de SQLite) a dict (Supabase Payload).
        Basado en el esquema de DBManager v3.0:
        0:id, 1:service, 2:username, 3:secret, 4:nonce, 5:integrity, 6:notes, 
        7:updated, 8:deleted, 9:owner_name, 10:synced, 11:is_private, 12:vault_id,
        13:key_type, 14:cloud_id, 15:owner_id
        """
        return {
            "id": row[14] if len(row) > 14 and row[14] else None, # cloud_id
            "service": row[1],
            "username": row[2],
            "secret_blob": row[3],
            "nonce_blob": row[4],
            "notes": row[6],
            "owner_name": str(row[9]).upper() if len(row) > 9 else "UNKNOWN",
            "is_private": row[11] if len(row) > 11 else 0,
            "deleted": row[8] if len(row) > 8 else 0,
            "vault_id": row[12] if len(row) > 12 else self.sm.current_vault_id,
            "updated_at": row[7] if len(row) > 7 else int(time.time()),
            "owner_id": row[15] if len(row) > 15 else None
        }

    def sync_audit_logs(self):
        if not self.check_internet(): return
        logs = self.sm.get_pending_audit_logs()
        if logs:
            # FIX: Mapping correcto según AuditRepository (l[6]=details, l[7]=device_info)
            payload = []
            for l in logs:
                payload.append({
                    "timestamp": l[1],
                    "user_name": l[2],
                    "action": l[3],
                    "service": l[4],      # Antes 'target_user' (confuso)
                    "status": l[5],
                    "details": l[6],      # l[6] es el campo Details en SQLite
                    "device_info": l[7],  # l[7] es el campo Device Info en SQLite
                    "user_id": l[9]
                })
            self.client.post_records(self.audit_table, payload)
            self.sm.mark_audit_logs_as_synced()

    def get_global_audit_logs(self, limit=500):
        """Obtiene los logs de auditoría globales del nodo central (ADMIN ONLY)."""
        if not self.check_internet(): return []
        try:
            # Ordenar por timestamp descendente
            return self.client.get_records(self.audit_table, f"order=timestamp.desc&limit={limit}")
        except Exception as e:
            logger.error(f"Error fetching global audit logs: {e}")
            return []

    def get_active_sessions(self):
        """Obtiene y agrupa los latidos recientes por dispositivo para mostrar sesiones únicas."""
        try:
            # 1. Filtro Agresivo: Solo eventos de los últimos 5 minutos (300s)
            now = int(time.time())
            cutoff = now - 300 
            
            # Obtener registros recientes (limitamos para no saturar, pero el filtro de tiempo es la clave)
            raw_logs = self.client.get_records(self.audit_table, f"timestamp=gt.{cutoff}&order=timestamp.desc&limit=100")
            
            sessions = {}
            for log in raw_logs:
                user = str(log.get("user_name") or "???").upper()
                device = log.get("device_info", "Unknown Device")
                
                # FIX: Ignorar si el 'device_info' parece ser un mensaje de error o detalle (por logs corruptos anteriores)
                # Si el campo tiene espacios largos o palabras de acción, lo descartamos de la agrupación de sesiones
                if len(device) > 30 or "Sesión" in device or "Login" in device:
                    continue
                session_key = f"{user}@{device}"
                
                if session_key not in sessions:
                    is_revoked = log.get("action") in ["KICK", "REVOKE", "EMERGENCY_LOCK"]
                    
                    sessions[session_key] = {
                        "username": user,
                        "device_name": device,
                        "ip_address": log.get("ip_address") or "---",
                        "last_seen": log.get("timestamp", 0),
                        "status": log.get("status", "OFFLINE"),
                        "is_revoked": is_revoked
                    }
            
            return list(sessions.values())
        except Exception as e:
            logger.error(f"Error aggregating active sessions: {e}")
            return []

    def revoke_session(self, target_user, target_device):
        """Envía una señal de revocación para un dispositivo específico."""
        if not self.check_internet(): return False
        try:
            payload = {
                "timestamp": int(time.time()),
                "user_name": str(target_user).upper(),
                "action": "KICK",
                "status": "REVOKED",
                "device_info": target_device,
                "details": f"Revocation issued by {self.sm.current_user}"
            }
            self.client.post_records(self.audit_table, [payload])
            return True
        except Exception as e:
            logger.error(f"Revocation Error: {e}")
            return False

    def check_revocation_status(self):
        """Verifica si el acceso del usuario ha sido revocado en el nodo central."""
        if not self.check_internet(): return False
        try:
            u_id = self.sm.current_user_id
            v_id = self.sm.current_vault_id
            if u_id and v_id:
                # 1. Verificar acceso a bóveda (Kill Switch de permisos)
                res = self.client.get_records("vault_access", f"select=id&user_id=eq.{u_id}&vault_id=eq.{v_id}")
                if len(res) == 0: return True # Revocado

            # 2. Verificar si hay un evento KICK reciente para este dispositivo
            import socket
            hostname = socket.gethostname()
            curr_user = (self.sm.current_user or "").upper()
            if not curr_user: return False
            
            kicks = self.client.get_records(self.audit_table, f"select=id&action=eq.KICK&user_name=eq.{curr_user}&device_info=eq.{hostname}&limit=1")
            return len(kicks) > 0
            
        except Exception as e:
            logger.error(f"Error checking revocation: {e}")
            return False

    def _get_public_ip(self):
        """Obtiene la IP pública del cliente con fallback a IP local."""
        try:
            import requests
            response = requests.get('https://api.ipify.org?format=json', timeout=3)
            return response.json().get('ip', 'Unknown')
        except:
            # Fallback a IP local si no hay internet o el servicio falla
            try:
                import socket
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
                return ip
            except:
                return "Unknown"
    
    def send_heartbeat(self, action="HEARTBEAT", status="ONLINE"):
        """Registra la actividad de la sesión en el nodo central para telemetría de seguridad."""
        if not self.check_internet(): return
        try:
            import socket
            
            # Capturar IP address
            ip_address = self._get_public_ip()
            
            payload = {
                "timestamp": int(time.time()),
                "user_name": str(self.sm.current_user or "").upper(),
                "action": action,
                "status": status,
                "device_info": socket.gethostname(),
                # "ip_address": ip_address,  # [PENDING MIGRATION] Enable after running migration_ip_address.sql
                "details": f"Session Activity Tracker | Role: {getattr(self.sm, 'user_role', 'user')}"
            }
            self.client.post_records(self.audit_table, [payload])
        except Exception as e:
            logger.error(f"Heartbeat Error: {e}")
    
