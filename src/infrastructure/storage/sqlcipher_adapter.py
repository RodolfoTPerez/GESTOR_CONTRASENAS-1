import pysqlcipher3
from pathlib import Path
from src.infrastructure.crypto.memory_wipe import secure_zero

class SQLCipherAdapter:
    def __init__(self, db_path: Path, key: bytes):
        self.conn = pysqlcipher3.connect(db_path)
        self.conn.execute(f"PRAGMA key = \"x'{key.hex()}'\";")
        self.conn.execute("PRAGMA cipher_page_size = 4096;")
        self.conn.execute("PRAGMA kdf_iter = 256000;")
        self.conn.execute("PRAGMA cipher_hmac_algorithm = HMAC_SHA512;")

    def init_schema(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS secrets (
            id TEXT PRIMARY KEY,
            service TEXT,
            username TEXT,
            ciphertext BLOB,
            nonce BLOB,
            salt BLOB,
            created_at TEXT,
            updated_at TEXT,
            deleted INTEGER DEFAULT 0
        );
        """)
        self.conn.commit()