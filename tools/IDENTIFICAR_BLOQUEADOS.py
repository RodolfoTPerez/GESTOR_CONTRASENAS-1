
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.infrastructure.secrets_manager import SecretsManager

def identify_locked_secrets():
    print("=== IDENTIFICACIÓN DE SECRETOS BLOQUEADOS ===")
    
    # Suponemos que el usuario es RODOLFO y el pass es RODOLFO (basado en fix_definition_keys.py)
    password = "RODOLFO" 
    username = "RODOLFO"
    
    sm = SecretsManager()
    sm.set_active_user(username, password)
    
    records = sm.get_all()
    locked = [r for r in records if r.get("secret") == "[Bloqueado 🔑]"]
    
    if not locked:
        print("No se encontraron secretos bloqueados.")
        return

    print(f"\nSe encontraron {len(locked)} secretos bloqueados:")
    for r in locked:
        print(f"ID: {r['id']} | Servicio: {r['service']} | Usuario: {r['username']} | Dueño: {r.get('owner_name')}")
    
    print("\nEstos registros probablemente fueron creados con una llave temporal (KEK) errónea")
    print("mientras el sistema estaba en estado degradado.")

if __name__ == "__main__":
    identify_locked_secrets()
