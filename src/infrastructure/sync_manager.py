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

    def sync_pending_users(self):
        """Sincroniza usuarios creados offline (synced=0) a Supabase."""
        if hasattr(self.sm, 'session'): self.sm.session.start_operation()
        try:
            if not self.check_internet():
                logger.warning("[User Sync] No internet, skipping pending user sync")
                return 0
            
            cursor = self.sm.conn.execute("""
                SELECT username, password_hash, salt, vault_salt, role, protected_key, vault_id, user_id
                FROM users 
                WHERE synced = 0
            """)
            pending_users = cursor.fetchall()
            
            if not pending_users:
                return 0
            
            # 1. Collect and preparation of user payloads
            user_payloads = []
            user_map = {} # Local username -> Row data
            
            for row in pending_users:
                username = row[0]
                user_map[username] = row
                payload = {
                    "username": username,
                    "password_hash": row[1],
                    "salt": row[2],
                    "vault_salt": row[3],
                    "role": row[4] or "user",
                    "active": True,
                    "vault_id": row[6]
                }
                if row[5]:
                    import base64
                    protected_bytes = self.sm._ensure_bytes(row[5])
                    payload["protected_key"] = base64.b64encode(protected_bytes).decode('ascii')
                user_payloads.append(payload)

            # 2. Batch Insert Users
            synced_count = 0
            if user_payloads:
                res = self.client.post_records("users", user_payloads, merge_duplicates=False)
                if not res or not res.get("data"):
                    logger.error("[User Sync] Batch user creation failed: No data returned")
                    return 0
                
                # 3. Process results and prepare Vault Access batch
                vault_payloads = []
                update_queries = []
                
                for cloud_user in res["data"]:
                    username = cloud_user["username"]
                    real_user_id = cloud_user["id"]
                    row = user_map.get(username)
                    
                    if row:
                        # Prepare Vault Access if SVK exists
                        if row[5] and row[6]:
                            protected_bytes = self.sm._ensure_bytes(row[5])
                            vault_payloads.append({
                                "user_id": real_user_id,
                                "vault_id": row[6],
                                "wrapped_master_key": protected_bytes.hex()
                            })
                        
                        update_queries.append((real_user_id, username))
                        synced_count += 1

                # 4. Batch Insert Vault Access
                if vault_payloads:
                    try:
                        self.client.post_records("vault_access", vault_payloads, merge_duplicates=True)
                        logger.info(f"[User Sync] Batched {len(vault_payloads)} vault access records.")
                    except Exception as va_err:
                        logger.error(f"[User Sync] Batch vault_access failure: {va_err}")

                # 5. Atomic Local Update
                if update_queries:
                    self.sm.conn.execute("BEGIN TRANSACTION")
                    try:
                        for u_id, u_name in update_queries:
                            self.sm.conn.execute("UPDATE users SET user_id = ?, synced = 1 WHERE username = ?", (u_id, u_name))
                        self.sm.conn.commit()
                    except Exception as e:
                        self.sm.conn.execute("ROLLBACK")
                        logger.error(f"[User Sync] Local DB Update failed: {e}")
                        return 0
            
            if synced_count > 0:
                logger.info(f"[User Sync] Successfully synced {synced_count} pending user(s)")
            
            return synced_count
        finally:
            if hasattr(self.sm, 'session'): self.sm.session.end_operation()
    
    def sync_pending_deletes(self):
        """Sync deletions that were made offline to Supabase."""
        if not self.check_internet():
            logger.debug("[Delete Sync] No internet, skipping pending delete sync")
            return 0
        
        try:
            # Get pending deletes
            cursor = self.sm.conn.execute("SELECT id, cloud_id FROM pending_deletes")
            pending = cursor.fetchall()
            
            if not pending:
                return 0
            
            synced_count = 0
            for row in pending:
                delete_id, cloud_id = row
                try:
                    # Delete from Supabase
                    self.client.delete_record(self.table, cloud_id)
                    logger.info(f"[Delete Sync] Deleted cloud record {cloud_id}")
                    
                    # Remove from pending_deletes
                    self.sm.conn.execute("DELETE FROM pending_deletes WHERE id=?", (delete_id,))
                    self.sm.conn.commit()
                    synced_count += 1
                    
                except Exception as e:
                    logger.error(f"[Delete Sync] Failed to delete {cloud_id}: {e}")
            
            if synced_count > 0:
                logger.info(f"[Delete Sync] Synced {synced_count} offline deletions to cloud")
            
            return synced_count
            
        except Exception as e:
            logger.error(f"[Delete Sync] Error in sync_pending_deletes: {e}")
            return 0

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
        if hasattr(self.sm, 'session'): self.sm.session.start_operation()
        try:
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
                    "vault_id": s.get("vault_id") or self.sm.current_vault_id,
                    "integrity_hash": s.get("integrity_hash"),
                    "version": s.get("version")
                }
                payload.append(item)

            if payload:
                if progress_callback: progress_callback(90, "Uploading data...")
                self.client.post_records(self.table, payload)
            
            if progress_callback: progress_callback(100, "Backup complete.")
            self.sync_audit_logs()
        finally:
            if hasattr(self.sm, 'session'): self.sm.session.end_operation()

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
        if hasattr(self.sm, 'session'): self.sm.session.start_operation()
        try:
            if not self.check_internet(): raise ConnectionError("No internet.")
            remote = self.client.get_records(self.table)
            if not remote: raise Exception("Remote node is empty.")

            if progress_callback: progress_callback(10, "Preparing local storage...")
            total = len(remote)
            
            # [AREA 4] ATOMIC STAGING PATTERN
            # Create a staging table with exactly the same schema as 'secrets'
            # We use a temporary table to avoid data loss if the network fails midway.
            try:
                self.sm.conn.execute("DROP TABLE IF EXISTS secrets_staging")
                self.sm.conn.execute("CREATE TABLE secrets_staging AS SELECT * FROM secrets WHERE 0")
                
                for i, s in enumerate(remote):
                    if progress_callback and i % 5 == 0:
                        progress_callback(20 + int((i/total)*70), f"Restoring: {s.get('service')}")
                    
                    nonce, cipher = self._decode_secret(s.get("secret", ""))
                    
                    # Calculate integrity_hash if missing from cloud
                    integrity_hash = s.get("integrity_hash")
                    if not integrity_hash:
                        import hashlib
                        integrity_hash = hashlib.sha256(cipher).hexdigest()
                        logger.info(f"Generated missing integrity_hash during restore for {s.get('service')}: {integrity_hash[:16]}...")
                    
                    params = (
                        s["service"], s["username"], cipher, nonce, int(time.time()),
                        1 if str(s.get("deleted")).lower() in ("1", "true", "t") else 0,
                        integrity_hash, s.get("notes"), s.get("owner_name") or self.sm.current_user,
                        1, 1 if str(s.get("is_private")).lower() in ("1", "true", "t") else 0,
                        s.get("vault_id"), s.get("id"), s.get("version")
                    )
                    self.sm.conn.execute("""
                        INSERT INTO secrets_staging 
                        (service, username, secret, nonce, updated_at, deleted, integrity_hash, notes, owner_name, synced, is_private, vault_id, cloud_id, version) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, params)

                # ATOMIC SWAP: Execute the swap inside a transaction
                if progress_callback: progress_callback(95, "Committing changes...")
                
                self.sm.conn.execute("BEGIN TRANSACTION")
                try:
                    self.sm.conn.execute("DELETE FROM secrets")
                    self.sm.conn.execute("INSERT INTO secrets SELECT * FROM secrets_staging")
                    self.sm.conn.execute("COMMIT")
                    logger.info(f"Atomic restore complete. {total} records swapped.")
                except Exception as e:
                    self.sm.conn.execute("ROLLBACK")
                    raise e
                finally:
                    self.sm.conn.execute("DROP TABLE IF EXISTS secrets_staging")
                    
                if progress_callback: progress_callback(100, "Restore complete.")
                
            except Exception as e:
                logger.error(f"Restoration failed: {e}")
                self.sm.conn.execute("DROP TABLE IF EXISTS secrets_staging")
                raise e

        finally:
            if hasattr(self.sm, 'session'): self.sm.session.end_operation()

    def sync(self, progress_callback=None, cloud_user_id=None):
        if hasattr(self.sm, 'session'): self.sm.session.start_operation()
        try:
            if not self.check_internet(): raise ConnectionError("No internet.")
            self._refresh_identity_headers()
            # Fetch user profile to get the cloud_user_id and username for _sync_shared_keys
            username = self.sm.current_user
            user_profile = {}
            if username:
                res = self.client.get_records("users", f"select=id&username=ilike.{username}")
                if res:
                    user_profile = res[0]

            if user_profile.get('id'):
                self._sync_shared_keys(cloud_user_id=user_profile['id'], username=username)
            else:
                # Fallback to existing behavior if user profile not found or no ID
                self._sync_shared_keys(cloud_user_id=cloud_user_id)
            
            self.sm.refresh_vault_context()
            
            # CRITICAL: Sync pending deletes FIRST (from offline deletions)
            self.sync_pending_deletes()

            if progress_callback: progress_callback(5, "Checking for changes...")
            
            # CRITICAL: Push local changes FIRST (including deletes) before pulling from cloud
            # This prevents deleted records from being re-downloaded
            local_mine = self.sm.get_all_encrypted(only_mine=True)
            has_local_changes = any(not r.get("synced") or r.get("deleted") for r in local_mine)

            uploaded = {"success": 0, "failed": 0}
            if has_local_changes:
                if progress_callback: progress_callback(30, "Uploading local changes...")
                uploaded = self._push_local_to_cloud()
            
            # THEN pull from cloud (after local deletes are synced)
            if progress_callback: progress_callback(60, "Downloading cloud changes...")
            downloaded = self._pull_cloud_to_local()
            
            self.sync_audit_logs()
            if progress_callback: progress_callback(100, f"Sync finished. ↑{uploaded['success']} ↓{downloaded}")
            return {"uploaded": uploaded["success"], "downloaded": downloaded, "errors": uploaded["failed"]}
        finally:
            if hasattr(self.sm, 'session'): self.sm.session.end_operation()

    def _sync_shared_keys(self, cloud_user_id=None, username=None):
        try:
            u_id = cloud_user_id
            active_user = username or self.sm.current_user
            
            if not u_id and active_user:
                res = self.client.get_records("users", f"select=id&username=ilike.{active_user}")
                if res: u_id = res[0]['id']
            
            if not u_id: return

            # [HEALING] Ensure local profile (and vault_salt) is synced before key unwrap attempts
            # This prevents "Phantom Salt" mismatches during vault access updates.
            from src.infrastructure.user_manager import UserManager
            um = UserManager(self.sm)
            cloud_profile = self.client.get_records("users", f"select=*&id=eq.{u_id}")
            cloud_salt = None
            if cloud_profile:
                # Capture the normalized salt from user manager
                cloud_salt = um.sync_user_to_local(active_user, cloud_profile[0])

            accesses = self.client.get_records("vault_access", f"select=*&user_id=eq.{u_id}")
            for acc in accesses:
                v_id = acc.get("vault_id")
                w_key = acc.get("wrapped_master_key")
                if v_id and w_key:
                    logger.info(f"[Sync] Persisting access to vault {v_id}")
                    # [HEALING] If the current session has no vault key, it's likely a sync conflict 
                    # preventing recovery. We force the cloud key if the local unwrap failed.
                    force_update = (self.sm.current_user is not None and self.sm.vault_key is None)
                    if force_update:
                        logger.info(f"[Sync] Local vault key missing or broken. Forcing cloud key overwrite for {v_id}.")
                    
                    self.sm.save_vault_access_local(
                        v_id, 
                        bytes.fromhex(w_key) if isinstance(w_key, str) else w_key, 
                        synced=1,
                        force=force_update,
                        vault_salt=cloud_salt if force_update else None
                    )
        except Exception as e: logger.error(f"Error syncing keys: {e}")

    def _push_local_to_cloud(self):
        stats = {"success": 0, "failed": 0}
        for rec in self.sm.get_all_encrypted(only_mine=True):
            if rec.get("synced"): continue
            
            try:
                # Handle deleted records separately
                if rec.get("deleted"):
                    # Delete from Supabase if it has a cloud_id
                    if rec.get("cloud_id"):
                        self.delete_from_supabase(rec["id"])
                        logger.info(f"Deleted record {rec['id']} from Supabase (offline delete sync)")
                    
                    # Mark as synced and remove from local DB
                    self.sm.conn.execute("DELETE FROM secrets WHERE id=?", (rec["id"],))
                    self.sm.conn.commit()
                    stats["success"] += 1
                else:
                    # Upload normal record
                    if self._upload_record(rec):
                        self.sm.mark_as_synced(rec["id"], 1)
                        stats["success"] += 1
            except Exception as e:
                logger.error(f"Error syncing record {rec.get('id')}: {e}")
                stats["failed"] += 1
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
            
            # Calculate integrity_hash if missing from cloud
            integrity_hash = rr.get("integrity_hash")
            if not integrity_hash:
                import hashlib
                integrity_hash = hashlib.sha256(cipher).hexdigest()
                logger.info(f"Generated missing integrity_hash for {rr['service']}: {integrity_hash[:16]}...")
            
            self.sm.add_secret_encrypted(
                service=rr["service"],
                username=rr["username"],
                secret_blob=cipher,
                nonce_blob=nonce,
                integrity=integrity_hash,
                notes=rr.get("notes"),
                is_private=1 if str(rr.get("is_private")).lower() in ("1", "true", "t") else 0,
                owner_name=rr.get("owner_name"),
                vault_id=rr.get("vault_id"),
                deleted=rr.get("deleted", 0),
                synced=1,
                cloud_id=rr["id"],
                version=rr.get("version")
            )
            count += 1
        return count


    def _upload_record(self, rec):
        c_id = rec.get("cloud_id")
        
        # Prepare the payload
        payload = {
            "service": rec["service"], "username": rec["username"],
            "secret": self._encode_secret(rec["nonce_blob"], rec["secret_blob"]),
            "notes": rec.get("notes"), "updated_at": int(time.time()),
            "owner_name": str(rec.get("owner_name") or self.sm.current_user or "unknown").upper(),
            "is_private": rec.get("is_private", 0), "deleted": rec.get("deleted", 0),
            "vault_id": rec.get("vault_id") or self.sm.current_vault_id,
            "integrity_hash": rec.get("integrity_hash") or rec.get("integrity"),
            "version": rec.get("version")
        }
        
        try:
            if c_id:
                # Record already exists in cloud - UPDATE it
                url = f"{self.client.supabase_url}/rest/v1/{self.table}?id=eq.{c_id}"
                headers = self.client.headers.copy()
                headers["Prefer"] = "return=minimal"
                
                r = self.client.session.patch(url, headers=headers, json=payload)
                if r.status_code not in (200, 204):
                    logger.error(f"Failed to update record {c_id}: {r.status_code} - {r.text}")
                    return False
                logger.info(f"Updated record {c_id} in Supabase")
            else:
                # New record - INSERT it
                c_id = self._ensure_cloud_id(rec)
                payload["id"] = c_id
                
                # Insert and verify it was created
                response = self.client.post_records(self.table, [payload])
                
                # Verify the record was actually inserted
                if response.status_code in (200, 201):
                    # Double-check by querying Supabase
                    try:
                        verify_url = f"{self.client.supabase_url}/rest/v1/{self.table}?id=eq.{c_id}"
                        verify_response = self.client.session.get(verify_url, headers=self.client.headers)
                        if verify_response.status_code == 200:
                            data = verify_response.json()
                            if data and len(data) > 0:
                                logger.info(f"Inserted new record {c_id} in Supabase (verified)")
                            else:
                                logger.error(f"Insert reported success but record {c_id} not found in Supabase")
                                return False
                        else:
                            logger.warning(f"Could not verify insert for {c_id}, assuming success")
                    except Exception as verify_err:
                        logger.warning(f"Could not verify insert for {c_id}: {verify_err}, assuming success")
                else:
                    logger.error(f"Failed to insert record {c_id}: {response.status_code} - {response.text}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error uploading record: {e}")
            return False

    def sync_single_record(self, record_id):
        if hasattr(self.sm, 'session'): self.sm.session.start_operation()
        try:
            if not self.check_internet(): return
            row = self.sm.conn.execute("SELECT * FROM secrets WHERE id=?", (record_id,)).fetchone()
            if not row: return
            rec = self._row_to_dict(row)
            self._upload_record(rec)
            self.sm.conn.execute("UPDATE secrets SET synced=1 WHERE id=?", (record_id,))
            self.sm.conn.commit()
        finally:
            if hasattr(self.sm, 'session'): self.sm.session.end_operation()

    def _row_to_dict(self, row):
        """
        Mapeo robusto de row (tuple de SQLite) a dict (Supabase Payload).
        Basado en el esquema de DBManager v3.0:
        0:id, 1:service, 2:username, 3:secret, 4:nonce, 5:integrity, 6:notes, 
        7:updated, 8:deleted, 9:owner_name, 10:synced, 11:is_private, 12:vault_id,
        13:key_type, 14:cloud_id, 15:owner_id, 16:version
        """
        return {
            "id": row[0],  # Local SQLite ID
            "cloud_id": row[14] if len(row) > 14 else None,  # Cloud UUID
            "service": row[1],
            "username": row[2],
            "secret_blob": row[3],
            "nonce_blob": row[4],
            "integrity_hash": row[5],
            "notes": row[6],
            "owner_name": str(row[9]).upper() if len(row) > 9 else "UNKNOWN",
            "is_private": row[11] if len(row) > 11 else 0,
            "deleted": row[8] if len(row) > 8 else 0,
            "vault_id": row[12] if len(row) > 12 else self.sm.current_vault_id,
            "updated_at": row[7] if len(row) > 7 else int(time.time()),
            "owner_id": row[15] if len(row) > 15 else None,
            "version": row[16] if len(row) > 16 else None
        }

    def sync_audit_logs(self):
        if hasattr(self.sm, 'session'): self.sm.session.start_operation()
        try:
            if not self.check_internet(): return
            logs = self.sm.get_pending_audit_logs()
            if not logs: return
            
            # Get valid user_ids from Supabase to avoid foreign key violations
            valid_user_ids = set()
            try:
                users_response = self.client.get_records("users", params="select=id")
                if users_response and len(users_response) > 0:
                    valid_user_ids = {u["id"] for u in users_response}
            except Exception as e:
                logger.warning(f"Could not fetch valid user_ids, syncing without validation: {e}")
            
            # FIX: Mapping correcto según AuditRepository (l[6]=details, l[7]=device_info)
            payload = []
            skipped_count = 0
            for l in logs:
                user_id = l[9]
                
                # Skip audit logs with invalid/orphaned user_id
                if user_id and valid_user_ids and user_id not in valid_user_ids:
                    logger.warning(f"Skipping audit log with orphaned user_id: {user_id}")
                    skipped_count += 1
                    continue
                
                payload.append({
                    "timestamp": l[1],
                    "user_name": l[2],
                    "action": l[3],
                    "service": l[4],      # Antes 'target_user' (confuso)
                    "status": l[5],
                    "details": l[6],      # l[6] es el campo Details en SQLite
                    "device_info": l[7],  # l[7] es el campo Device Info en SQLite
                    "user_id": user_id
                })
            
            if not payload:
                logger.info(f"No valid audit logs to sync (skipped {skipped_count} orphaned)")
                return
            
            try:
                self.client.post_records(self.audit_table, payload)
                self.sm.mark_audit_logs_as_synced()
                if skipped_count > 0:
                    logger.info(f"Synced {len(payload)} audit logs, skipped {skipped_count} orphaned")
            except Exception as e:
                err_str = str(e).lower()
                if "23503" in err_str or "foreign key" in err_str:
                    logger.error(f"Foreign key violation in audit sync (orphaned user_id): {e}")
                    # Mark as synced anyway to avoid infinite retry loop
                    self.sm.mark_audit_logs_as_synced()
                else:
                    raise
        finally:
            if hasattr(self.sm, 'session'): self.sm.session.end_operation()

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
        # Fast-fail if offline
        if not self.check_internet():
            logger.debug("Skipping active sessions check - offline mode")
            return []
        
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
                
                # Verificar si la sesión está revocada
                is_revoked = log.get("status") == "REVOKED"
                
                # Solo actualizar si no existe o si es más reciente
                if session_key not in sessions or log.get("timestamp", 0) > sessions[session_key]["last_seen"]:
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
            logger.debug(f"Error aggregating active sessions (offline): {e}")
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
            
            # Solo buscar expulsiones en los últimos 15 minutos para permitir re-ingreso
            recent_cutoff = int(time.time()) - 900
            kicks = self.client.get_records(
                self.audit_table, 
                f"select=id&action=eq.KICK&user_name=eq.{curr_user}&device_info=eq.{hostname}&timestamp=gt.{recent_cutoff}&limit=1"
            )
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
    
