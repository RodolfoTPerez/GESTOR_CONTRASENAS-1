from src.infrastructure.config.path_manager import PathManager

DB_PATH = PathManager.DATA_DIR / "passguardian-secure.db"

def unlock_vault() -> tuple[SQLCipherAdapter, bytes]:
    master = getpass.getpass("Master password: ")
    salt = generate_salt()
    key = derive_key(master, salt)
    db = SQLCipherAdapter(DB_PATH, key)
    db.init_schema()
    return db, key

def bootstrap_vault():
    logging.basicConfig(level=logging.INFO)
    db, key = unlock()
    logger.info(f"Vault unlocked successfully. Key length: {len(key)} bytes")

if __name__ == "__main__":
    bootstrap_vault()
