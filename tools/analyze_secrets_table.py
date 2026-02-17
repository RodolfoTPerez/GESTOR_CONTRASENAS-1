import sqlite3
import json

conn = sqlite3.connect(r'C:\PassGuardian_v2\data\vault_rodolfo.db')

# Get schema
cursor = conn.execute('PRAGMA table_info(secrets)')
schema = cursor.fetchall()
print("=== SCHEMA DE LA TABLA SECRETS ===")
for col in schema:
    print(f"{col[0]:2d}. {col[1]:20s} {col[2]:10s} {'NOT NULL' if col[3] else ''}")

# Get last 5 records with all fields
cursor = conn.execute('''
    SELECT 
        id, service, username, 
        LENGTH(secret) as secret_len, 
        LENGTH(nonce) as nonce_len, 
        integrity_hash, 
        notes, 
        updated_at, 
        deleted, 
        owner_name, 
        synced, 
        is_private, 
        vault_id, 
        key_type,
        cloud_id, 
        owner_id, 
        version 
    FROM secrets 
    ORDER BY id DESC 
    LIMIT 5
''')

cols = [d[0] for d in cursor.description]
records = cursor.fetchall()

print("\n=== ÚLTIMOS 5 REGISTROS ===")
for row in records:
    record = dict(zip(cols, row))
    print(f"\n--- ID: {record['id']} | Service: {record['service']} ---")
    for key, value in record.items():
        if key == 'integrity_hash':
            display = f"{value[:16]}..." if value else "[VACIO]"
        elif key == 'cloud_id':
            display = f"{value[:8]}..." if value else "[VACIO]"
        elif key == 'vault_id':
            display = f"{value[:8]}..." if value else "[VACIO]"
        else:
            display = value
        status = "[OK]" if value else "[FALTA]"
        print(f"  {key:20s}: {display} {status if key in ['integrity_hash', 'cloud_id'] else ''}")

conn.close()
