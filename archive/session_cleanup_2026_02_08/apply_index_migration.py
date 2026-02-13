
import sqlite3

def apply_migration():
    db_paths = [
        r"C:\PassGuardian_v2\data\vault_rodolfo.db",
        r"C:\PassGuardian_v2\data\vault_kiki.db",
        r"C:\PassGuardian_v2\data\vault_lllllll.db"
    ]
    
    for db_path in db_paths:
        try:
            print(f"Migrating {db_path}...")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 1. Drop old index
            cursor.execute("DROP INDEX IF EXISTS idx_unique_secret")
            
            # 2. Drop if idx_unique_service exists (to re-create it clean)
            cursor.execute("DROP INDEX IF EXISTS idx_unique_service")
            
            # 3. Create NEW strict index
            # [IMPORTANT] This will fail if there are duplicates!
            try:
                cursor.execute("CREATE UNIQUE INDEX idx_unique_service ON secrets (service)")
                print(f"  Successfully created idx_unique_service.")
            except sqlite3.IntegrityError:
                print(f"  FAILED: Duplicates found in {db_path}. Cleaning up duplicates (keeping newest)...")
                # Deduplicate: Keep the maximum ID (newest) for each service
                cursor.execute("""
                    DELETE FROM secrets 
                    WHERE id NOT IN (
                        SELECT MAX(id) 
                        FROM secrets 
                        GROUP BY service
                    )
                """)
                cursor.execute("CREATE UNIQUE INDEX idx_unique_service ON secrets (service)")
                print(f"  Cleanup successful. Index created.")
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"  Error migrating {db_path}: {e}")

if __name__ == "__main__":
    apply_migration()
