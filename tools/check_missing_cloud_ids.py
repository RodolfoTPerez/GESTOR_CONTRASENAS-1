import sqlite3

conn = sqlite3.connect(r'C:\PassGuardian_v2\data\vault_rodolfo.db')

# Verificar registros sin cloud_id
cursor = conn.execute('''
    SELECT COUNT(*) as total, 
           SUM(CASE WHEN cloud_id IS NULL OR cloud_id = '' THEN 1 ELSE 0 END) as sin_cloud_id,
           SUM(CASE WHEN synced = 0 THEN 1 ELSE 0 END) as no_synced
    FROM secrets 
    WHERE deleted = 0
''')

row = cursor.fetchone()
print(f'Total registros activos: {row[0]}')
print(f'Sin cloud_id: {row[1]}')
print(f'No sincronizados (synced=0): {row[2]}')

# Mostrar algunos registros sin cloud_id
print('\n=== REGISTROS SIN CLOUD_ID ===')
cursor = conn.execute('''
    SELECT id, service, username, synced, cloud_id
    FROM secrets 
    WHERE deleted = 0 AND (cloud_id IS NULL OR cloud_id = '')
    LIMIT 5
''')

for row in cursor:
    print(f"ID: {row[0]}, Service: {row[1]}, User: {row[2]}, Synced: {row[3]}, cloud_id: {row[4]}")

conn.close()
