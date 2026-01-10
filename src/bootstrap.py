import getpass, keyring, uuid
from src.infrastructure.crypto.argon2_kdf import derive_key, generate_salt
from src.infrastructure.storage.sqlcipher_adapter import SQLCipherAdapter
from pathlib import Path

DB_PATH = Path(r"C:\PassGuardian\passguardian-secure.db")

def unlock_vault() -> tuple[SQLCipherAdapter, bytes]:
    master = getpass.getpass("Master password: ")
    salt = generate_salt()
    key = derive_key(master, salt)
    db = SQLCipherAdapter(DB_PATH, key)
    db.init_schema()
    return db, key

if __name__ == "__main__":
    db, key = unlock_vault()
    print("Vault unlocked. Key length:", len(key))