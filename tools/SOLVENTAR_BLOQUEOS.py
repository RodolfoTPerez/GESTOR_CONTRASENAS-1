
import os
import sys
import sqlite3
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.infrastructure.secrets_manager import SecretsManager

def solventar_bloqueos():
    print("="*60)
    print("ASISTENTE DE SOLVENCIA TÉCNICA - PASSGUARDIAN")
    print("="*60)
    
    password = input("Introduce tu contraseña maestra para validar descifrado: ")
    username = "RODOLFO" # Asumimos Rodolfo como usuario principal
    
    try:
        sm = SecretsManager()
        sm.set_active_user(username, password)
        
        records = sm.get_all()
        locked_ids = [r['id'] for r in records if r.get("secret") == "[Bloqueado 🔑]"]
        
        if not locked_ids:
            print("\n✅ ¡No se detectaron registros bloqueados! Todo está en orden.")
            return

        print(f"\n⚠️ Se detectaron {len(locked_ids)} registros bloqueados que no coinciden con tu llave actual.")
        print("Estos registros suelen ser 'basura' de pruebas anteriores o cambios de clave incompletos.")
        
        for r in records:
            if r['id'] in locked_ids:
                print(f" - [ID {r['id']}] Servicio: {r['service']} | Usuario: {r['username']}")

        confirm = input(f"\n¿Deseas ELIMINAR estos {len(locked_ids)} registros para limpiar tu base de datos? (s/n): ")
        
        if confirm.lower() == 's':
            conn = sqlite3.connect(f"data/vault_{username.lower()}.db")
            for lid in locked_ids:
                conn.execute("DELETE FROM secrets WHERE id = ?", (lid,))
            conn.commit()
            conn.close()
            print(f"\n✅ ÉXITO: {len(locked_ids)} registros eliminados. El mensaje de error desaparecerá.")
        else:
            print("\nOperación cancelada. Los registros permanecen bloqueados.")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    solventar_bloqueos()
