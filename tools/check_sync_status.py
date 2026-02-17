import sqlite3

conn = sqlite3.connect(r'C:\PassGuardian_v2\data\vault_rodolfo.db')
cursor = conn.execute('''
    SELECT id, service, cloud_id, synced, LENGTH(integrity_hash) as hash_len 
    FROM secrets 
    WHERE owner_name="RODOLFO" 
    ORDER BY updated_at DESC 
    LIMIT 3
''')

print("=== ÚLTIMOS 3 REGISTROS ACTUALIZADOS ===")
for row in cursor:
    print(f"ID: {row[0]}, Service: {row[1]}, cloud_id: {row[2][:8] if row[2] else 'None'}..., synced: {row[3]}, hash_len: {row[4]}")

conn.close()
