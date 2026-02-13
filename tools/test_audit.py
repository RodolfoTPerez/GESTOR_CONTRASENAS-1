
from src.infrastructure.secrets_manager import SecretsManager
import os

def test_audit_visibility():
    sm = SecretsManager()
    # Forzamos conexión y carga de rol sin password
    sm.current_user = "RODOLFO"
    sm.reconnect("RODOLFO")
    profile = sm.get_local_user_profile("RODOLFO")
    sm.user_role = str(profile.get("role") or "user").lower()
    
    print(f"Current User: {sm.current_user}")
    print(f"Current Role: {sm.user_role}")
    
    logs = sm.get_audit_logs(limit=20)
    print(f"Retrieved {len(logs)} logs.")
    
    users_in_logs = set(l.get("user_name") for l in logs)
    print(f"Users in retrieved logs: {users_in_logs}")
    
    # Check if there are ANY kiki logs in the DB
    cursor = sm.conn.execute("SELECT COUNT(*) FROM security_audit WHERE user_name = 'KIKI'")
    kiki_count = cursor.fetchone()[0]
    print(f"Total KIKI logs in DB: {kiki_count}")

if __name__ == "__main__":
    test_audit_visibility()
