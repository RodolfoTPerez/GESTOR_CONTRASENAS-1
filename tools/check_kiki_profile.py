import sqlite3

# Check KIKI's user_id in local database
conn = sqlite3.connect(r'C:\PassGuardian_v2\data\vault_kiki.db')

print("=== KIKI's Local Profile ===")
cursor = conn.execute("SELECT username, user_id, synced, role FROM users WHERE username = 'KIKI'")
row = cursor.fetchone()
if row:
    print(f"Username: {row[0]}")
    print(f"User ID: {row[1]}")
    print(f"Synced: {row[2]}")
    print(f"Role: {row[3]}")
else:
    print("KIKI not found in local database")

print("\n=== Recent Security Audit Entries ===")
cursor = conn.execute("""
    SELECT timestamp, user_name, action, status, user_id 
    FROM security_audit 
    ORDER BY timestamp DESC 
    LIMIT 5
""")
for row in cursor:
    print(f"Time: {row[0]}, User: {row[1]}, Action: {row[2]}, Status: {row[3]}, UserID: {row[4]}")

conn.close()
