import os
import sqlite3
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag

import time
import json
import hashlib


class SecretsManager:
    def __init__(self, master_password: str):
        db_path = Path(__file__).resolve().parent.parent.parent / "passguardian.db"

        self.conn = sqlite3.connect(
            db_path,
            timeout=10,
            check_same_thread=False
        )

        self._create_meta_table()
        self._create_secrets_table()
        self._add_integrity_column()
        self._add_notes_column()

        salt = self._get_or_create_salt()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=200_000,
            backend=default_backend()
        )
        self.master_key = kdf.derive(master_password.encode("utf-8"))

    # -----------------------------
    # TABLAS
    # -----------------------------
    def _create_meta_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value BLOB
            )
        """)
        self.conn.commit()

    def _create_secrets_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS secrets (
                id INTEGER PRIMARY KEY,
                service TEXT,
                username TEXT,
                secret BLOB,
                nonce BLOB,
                remote_id TEXT,
                updated_at INTEGER,
                deleted INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()

    def _add_integrity_column(self):
        try:
            self.conn.execute("ALTER TABLE secrets ADD COLUMN integrity_hash TEXT")
            self.conn.commit()
        except Exception:
            pass

    def _add_notes_column(self):
        try:
            self.conn.execute("ALTER TABLE secrets ADD COLUMN notes TEXT")
            self.conn.commit()
        except Exception:
            pass

    # -----------------------------
    # SALT
    # -----------------------------
    def _get_or_create_salt(self):
        cur = self.conn.execute("SELECT value FROM meta WHERE key = 'salt'")
        row = cur.fetchone()
        if row:
            return row[0]

        salt = os.urandom(16)
        self.conn.execute("INSERT INTO meta (key, value) VALUES ('salt', ?)", (salt,))
        self.conn.commit()
        return salt

    # -----------------------------
    # CRUD
    # -----------------------------
    def add_secret(self, service, username, secret_plain, notes=None):
        nonce = os.urandom(12)
        aes = AESGCM(self.master_key)
        encrypted = aes.encrypt(nonce, secret_plain.encode("utf-8"), None)

        integrity_hash = hashlib.sha256(secret_plain.encode("utf-8")).hexdigest()

        self.conn.execute(
            """
            INSERT INTO secrets (service, username, secret, nonce, updated_at, deleted, integrity_hash, notes)
            VALUES (?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (service, username, encrypted, nonce, int(time.time()), integrity_hash, notes)
        )
        self.conn.commit()

    def update_secret(self, sid, service, username, secret_plain, notes=None):
        nonce = os.urandom(12)
        aes = AESGCM(self.master_key)
        encrypted = aes.encrypt(nonce, secret_plain.encode("utf-8"), None)

        integrity_hash = hashlib.sha256(secret_plain.encode("utf-8")).hexdigest()

        self.conn.execute(
            """
            UPDATE secrets
            SET service = ?, username = ?, secret = ?, nonce = ?, updated_at = ?, integrity_hash = ?, notes = ?
            WHERE id = ?
            """,
            (service, username, encrypted, nonce, int(time.time()), integrity_hash, notes, sid)
        )
        self.conn.commit()

    def delete_secret(self, sid):
        self.conn.execute("UPDATE secrets SET deleted = 1 WHERE id = ?", (sid,))
        self.conn.commit()

    def get_record(self, service, username):
        cur = self.conn.execute(
            """
            SELECT id, service, username, secret, nonce, integrity_hash, notes
            FROM secrets
            WHERE service = ? AND username = ? AND deleted = 0
            """,
            (service, username)
        )
        row = cur.fetchone()
        if not row:
            return None

        sid, service, username, secret_blob, nonce, integrity_hash, notes = row

        aes = AESGCM(self.master_key)
        plain = aes.decrypt(nonce, secret_blob, None).decode("utf-8")

        return {
            "id": sid,
            "service": service,
            "username": username,
            "secret": plain,
            "notes": notes
        }

    def get_all(self):
        cursor = self.conn.execute("""
            SELECT id, service, username, secret, nonce, integrity_hash, notes
            FROM secrets
            WHERE deleted = 0
            ORDER BY id ASC
        """)

        results = []

        for row_id, service, username, secret_blob, nonce, integrity_hash, notes in cursor:
            aes = AESGCM(self.master_key)

            try:
                plain = aes.decrypt(nonce, secret_blob, None).decode("utf-8")
            except InvalidTag:
                raise ValueError("La contraseña maestra es incorrecta o la base de datos está dañada.")

            results.append({
                "id": row_id,
                "service": service,
                "username": username,
                "secret": plain,
                "notes": notes
            })

        return results

    # -----------------------------
    # BACKUP LOCAL
    # -----------------------------
    def create_local_backup(self):
        secrets = self.get_all()
        data = json.dumps(secrets, ensure_ascii=False).encode("utf-8")

        nonce = os.urandom(12)
        aes = AESGCM(self.master_key)
        ciphertext = aes.encrypt(nonce, data, None)

        base_dir = Path(__file__).resolve().parent.parent.parent
        backups_dir = base_dir / "backups"
        backups_dir.mkdir(exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = backups_dir / f"backup_{timestamp}.enc"

        with open(backup_path, "wb") as f:
            f.write(nonce + ciphertext)

        return str(backup_path)

    def local_restore(self):
        base_dir = Path(__file__).resolve().parent.parent.parent
        backups_dir = base_dir / "backups"
        backups_dir.mkdir(exist_ok=True)

        files = sorted(backups_dir.glob("backup_*.enc"))
        if not files:
            raise FileNotFoundError("No se encontraron backups locales.")

        backup_path = files[-1]

        with open(backup_path, "rb") as f:
            data = f.read()

        nonce = data[:12]
        ciphertext = data[12:]

        aes = AESGCM(self.master_key)
        plain = aes.decrypt(nonce, ciphertext, None)
        secrets = json.loads(plain.decode("utf-8"))

        self.conn.execute("DELETE FROM secrets")
        self.conn.commit()

        for s in secrets:
            self.add_secret(
                s.get("service"),
                s.get("username"),
                s.get("secret"),
                s.get("notes")
            )

    # -----------------------------
    # CERRAR
    # -----------------------------
    def close(self):
        try:
            self.conn.close()
        except:
            pass
        self.master_key = None
