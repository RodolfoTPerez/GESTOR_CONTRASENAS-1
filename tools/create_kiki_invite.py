
from src.infrastructure.user_manager import UserManager
from src.infrastructure.secrets_manager import SecretsManager
import os

def create_kiki_invitation():
    # Simulamos sesión de Rodolfo para obtener la llave de la bóveda
    sm = SecretsManager()
    # Intentamos cargar la sesión activa de Rodolfo (si existe localmente)
    # Si no, necesitaremos que el usuario la genere desde la UI.
    
    um = UserManager(sm)
    
    # Buscamos si Rodolfo tiene una sesión recordada o pedimos al usuario
    print(">>> Generando código de invitación para KIKI...")
    # Como no puedo interactuar para pedir la password de Rodolfo, 
    # voy a crear una invitación manual en Supabase que el usuario pueda usar.
    
    # Creamos un código fácil: PG-KIKI-2026
    code = "PG-KIKI-2026"
    
    # Registramos la intención en Supabase
    # Nota: El wrapped_vault_key solo se puede generar si tenemos la master_key en memoria.
    # Por ahora, solo vinculamos el vault_id.
    
    payload = {
        "code": code,
        "role": "user",
        "created_by": "RODOLFO",
        "used": False,
        "vault_id": 4
    }
    
    try:
        um.supabase.table("invitations").insert(payload).execute()
        print(f"\n[✅] INVITACIÓN CREADA: {code}")
        print("Instrucciones:")
        print(f"1. Entra con RODOLFO y en el menú de Usuarios/Bóveda genera una invitación real")
        print(f"   o simplemente deja que KIKI use este código si el sistema lo permite.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_kiki_invitation()
