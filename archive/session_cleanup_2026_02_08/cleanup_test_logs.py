
import sqlite3

def cleanup_audit_logs():
    db_paths = [
        r"C:\PassGuardian_v2\data\vault_rodolfo.db",
        r"C:\PassGuardian_v2\data\vault_kiki.db",
        r"C:\PassGuardian_v2\data\vault_lllllll.db"
    ]
    
    invalid_id = "test-user-id-001"
    
    for db_path in db_paths:
        try:
            print(f"Checking {db_path} for invalid audit IDs...")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Count before
            cursor.execute("SELECT COUNT(*) FROM security_audit WHERE user_id = ?", (invalid_id,))
            count = cursor.fetchone()[0]
            
            if count > 0:
                cursor.execute("DELETE FROM security_audit WHERE user_id = ?", (invalid_id,))
                print(f"  Deleted {count} invalid test logs from {db_path}.")
                conn.commit()
            else:
                print(f"  No invalid logs found in {db_path}.")
            
            conn.close()
        except Exception as e:
            print(f"  Error processing {db_path}: {e}")

if __name__ == "__main__":
    cleanup_audit_logs()
