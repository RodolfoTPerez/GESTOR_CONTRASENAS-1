import os
import sys
import json
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

# Asegurar que el path incluya la raíz del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.infrastructure.secrets_manager import SecretsManager
from src.infrastructure.sync_manager import SyncManager
from config.config import SUPABASE_URL, SUPABASE_KEY

def diagnostico_sync_privado():
    print("="*80)
    print("DIAGNÓSTICO DE SINCRONIZACIÓN DE REGISTROS PRIVADOS")
    print("="*80)

    sm = SecretsManager()
    sm.set_active_user("RODOLFO", "RODOLFO") # Usuario de prueba
    
    sync = SyncManager(sm, SUPABASE_URL, SUPABASE_KEY)
    
    # Buscar el registro privado PENDIENTE
    cursor = sm.conn.execute("SELECT id, service, is_private, synced FROM secrets WHERE is_private = 1 AND synced = 0")
    row = cursor.fetchone()
    
    if not row:
        print("No se encontró ningún registro privado pendiente de sincronización.")
        # Verificar si hay alguno aunque NO esté pendiente
        cursor = sm.conn.execute("SELECT id, service, is_private, synced FROM secrets WHERE is_private = 1")
        row = cursor.fetchone()
        if not row:
            print("No hay registros privados en la base de datos local.")
            return
        else:
            print(f"Encontrado registro privado '{row[1]}' (ID: {row[0]}), pero ya está marcado como SYNC={row[3]}.")
            print("Forzando re-intento de sincronización...")
    
    record_id = row[0]
    service = row[1]
    
    print(f"\nIntentando sincronizar registro: {service} (ID: {record_id})")
    print("-" * 50)
    
    try:
        # Extraer los datos como lo hace SyncManager
        cursor = sm.conn.execute("SELECT * FROM secrets WHERE id = ?", (record_id,))
        row_data = cursor.fetchone()
        cols = [d[0] for d in cursor.description]
        rec = dict(zip(cols, row_data))
        
        # Preparar payload
        cloud_secret = sync._encode_secret(rec["nonce"], rec["secret"])
        
        payload = {
            "id": rec["cloud_id"],
            "service": rec["service"],
            "username": rec["username"],
            "secret": cloud_secret,
            "notes": rec.get("notes"),
            "updated_at": rec.get("updated_at"),
            "owner_name": (rec.get("owner_name") or "RODOLFO").upper(),
            "is_private": rec.get("is_private", 0),
            "deleted": rec.get("deleted", 0),
            "vault_id": rec.get("vault_id")
        }
        
        print(f"Payload preparado: {json.dumps(payload, indent=2)}")
        
        # Intentar POST manual para ver el error exacto
        headers = sync.headers.copy()
        headers["Prefer"] = "resolution=merge-duplicates"
        
        url = f"{sync.supabase_url}/rest/v1/secrets"
        print(f"\nEnviando a {url}...")
        
        import requests
        r = requests.post(url, headers=headers, data=json.dumps(payload))
        
        print(f"\nRESPUESTA SUPABASE:")
        print(f"Status Code: {r.status_code}")
        print(f"Body: {r.text}")
        
        if r.status_code in (200, 201, 204):
            print("\n¡ÉXITO! El registro se subió correctamente.")
            sm.mark_as_synced(record_id, 1)
            print("Estado local actualizado a SYNC=1")
        else:
            print("\n❌ FALLO: Supabase rechazó el registro.")
            if "policy" in r.text.lower() or "permission" in r.text.lower():
                print(">>> MOTIVO: Violación de política RLS.")
            elif "column" in r.text.lower():
                print(">>> MOTIVO: Error de esquema (faltan columnas).")
                
    except Exception as e:
        print(f"\nERROR DURANTE EL DIAGNÓSTICO: {e}")

if __name__ == "__main__":
    diagnostico_sync_privado()
