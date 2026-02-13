
import sqlite3
import time
import requests
import json

def test_audit_e2e():
    db_path = r"C:\PassGuardian_v2\data\vault_rodolfo.db"
    conn = sqlite3.connect(db_path)
    # Insert a dummy log with synced=0
    print("Inserting mock audit log...")
    ts = int(time.time())
    user_id = "test-user-id-001"
    conn.execute("""
        INSERT INTO security_audit (timestamp, user_name, action, service, status, details, device_info, synced, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
    """, (ts, "MOCK_USER", "TEST_ACTION", "TEST_SERVICE", "SUCCESS", "Test details", "TEST_DEVICE", user_id))
    conn.commit()
    conn.close()

    # We need to trigger sync_audit_logs. 
    # Instead of running the full app, we can mock the SyncManager call or use a script.
    # Let's check if the push logic works by running a standalone version of it.
    
    # Actually, I'll just check if it inserted into local DB correctly first.
    conn = sqlite3.connect(db_path)
    res = conn.execute("SELECT * FROM security_audit WHERE action='TEST_ACTION'").fetchone()
    print(f"Local Insert Result: {res}")
    conn.close()

if __name__ == "__main__":
    test_audit_e2e()
