# C:\PassGuardian\src\infrastructure\secrets_manager.py
import sqlite3
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import 
 

class SecretsManager:
    def __init__(self, master_password):
        self.master_key = master_password.encode()
        #self.conn = sqlite3.connect("config/local.db")
        from pathlib import Path
        DB_PATH = Path(__file__).resolve().parent.parent.parent / "passguardian.db"
        self.conn = sqlite3.connect(DB_PATH)
        self.create_table()

    def create_table(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS secrets (
            id INTEGER PRIMARY KEY,
            service TEXT,
            username TEXT,
            secret BLOB,
            nonce BLOB
        )
        """)
        self.conn.commit()

    def add_secret(self, service, username, secret_plain):
        nonce = os.urandom(12)
        aes = AESGCM(self.master_key.ljust(32, b'\0'))  # derivación simple
        secret_encrypted = aes.encrypt(nonce, secret_plain.encode(), None)
        self.conn.execute("INSERT INTO secrets (service, username, secret, nonce) VALUES (?, ?, ?, ?)",
                          (service, username, secret_encrypted, nonce))
        self.conn.commit()

    def get_all(self):
        cursor = self.conn.execute("SELECT service, username, secret, nonce FROM secrets")
        results = []
        for row in cursor:
            aes = AESGCM(self.master_key.ljust(32, b'\0'))
            secret_plain = aes.decrypt(row[3], row[2], None).decode()
            results.append({"service": row[0], "username": row[1], "secret": secret_plain})
        return results
