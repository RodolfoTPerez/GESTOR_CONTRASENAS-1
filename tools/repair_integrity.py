import sqlite3
import hashlib
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def repair_integrity_hashes():
    db_path = Path(r"C:\PassGuardian_v2\data\vault_rodolfo.db")
    if not db_path.exists():
        logger.error(f"Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Find records with missing integrity_hash
        cursor.execute("SELECT id, secret FROM secrets WHERE integrity_hash IS NULL OR integrity_hash = ''")
        records = cursor.fetchall()
        
        if not records:
            logger.info("No records found with missing integrity_hash.")
            return

        logger.info(f"Found {len(records)} records with missing integrity_hash. Repairing...")

        repaired_count = 0
        for sid, secret_blob in records:
            if not secret_blob:
                logger.warning(f"Record {sid} has no secret data. Skipping.")
                continue
            
            # Generate SHA-256 hash of the encrypted secret (BLOB)
            # This matches SecurityService.encrypt_data logic: integrity = hashlib.sha256(encrypted).hexdigest()
            new_hash = hashlib.sha256(secret_blob).hexdigest()
            
            cursor.execute("UPDATE secrets SET integrity_hash = ?, synced = 0 WHERE id = ?", (new_hash, sid))
            repaired_count += 1
            logger.info(f"Repaired record {sid}: {new_hash[:8]}...")

        conn.commit()
        conn.close()
        logger.info(f"Successfully repaired {repaired_count} records.")

    except Exception as e:
        logger.exception(f"An error occurred during repair: {e}")

if __name__ == "__main__":
    repair_integrity_hashes()
