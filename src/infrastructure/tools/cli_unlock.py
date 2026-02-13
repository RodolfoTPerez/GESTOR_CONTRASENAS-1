# src\infrastructure\tools\cli_unlock.py
import getpass
from pathlib import Path
from src.infrastructure.crypto.argon2_kdf import derive_key, generate_salt
from src.infrastructure.storage.sqlcipher_adapter import SQLCipherAdapter
import logging

logger = logging.getLogger(__name__)

DB_PATH = Path(r"C:\PassGuardian\passguardian-secure.db")

def unlock() -> tuple[SQLCipherAdapter, bytes]:
    master = getpass.getpass("Master password: ")
    salt   = generate_salt()
    key    = derive_key(master, salt)
    db     = SQLCipherAdapter(DB_PATH, key)
    db.init_schema()
    return db, key

# Si se ejecuta directamente corre la utilidad
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db, key = unlock()
    logger.info(f"Vault unlocked successfully. Key length: {len(key)} bytes")
