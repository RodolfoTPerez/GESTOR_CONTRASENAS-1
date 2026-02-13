import os
import sys
import base64
import secrets
import time
from pathlib import Path

# Add src to path
sys.path.append(os.getcwd())

from src.infrastructure.secrets_manager import SecretsManager
from src.infrastructure.user_manager import UserManager
from config.config import SUPABASE_URL, SUPABASE_KEY
from src.infrastructure.sync_manager import SyncManager

def generate_random_secrets(sm, count=100):
    services = ["Google", "Facebook", "Netflix", "Amazon", "Spotify", "GitHub", "LinkedIn", "Twitter", "Instagram", "Reddit", 
                "Microsoft", "Apple", "Adobe", "Slack", "Discord", "Zoom", "Twitch", "Uber", "Airbnb", "PayPal",
                "eBay", "Pinterest", "WhatsApp", "Dropbox", "Trello", "Asana", "Salesforce", "HubSpot", "Shopify", "Wordpress",
                "Medium", "Quora", "StackOverflow", "Bitbucket", "GitLab", "Heroku", "DigitalOcean", "AWS", "Azure", "Cloudflare"]
    
    usernames = ["user", "admin", "tester", "dev", "guest", "pro", "master", "rookie", "shadow", "ghost"]
    
    print(f">>> Generando {count} secretos...")
    for i in range(count):
        service = f"{services[i % len(services)]} {i // len(services) + 1}"
        username = f"{usernames[secrets.randbelow(len(usernames))]}@{service.lower().replace(' ', '')}.com"
        password = secrets.token_urlsafe(12)
        notes = f"Registro generado automáticamente #{i+1}"
        is_private = 1 if i < 50 else 0  # 50 privados, 50 públicos
        
        try:
            sm.add_secret(
                service=service,
                username=username,
                secret_plain=password,
                notes=notes,
                is_private=is_private
            )
        except Exception as e:
            print(f"Error al crear secreto {i+1}: {e}")
            break
    print(f">>> {count} secretos creados en DB local.")

def main():
    um = UserManager()
    sm = SecretsManager()
    um.sm = sm  # Vincular SM al UM
    
    users_to_process = [
        ("RODOLFO", "RODOLFO"), # Intentamos con el mismo nombre
        ("KIKI", "KIKI"),
        ("KAREN", "KAREN"),
        ("DANIEL", "DANIEL")
    ]
    
    for username, password in users_to_process:
        print(f"\n--- PROCESANDO USUARIO: {username} ---")
        
        # 1. Registrar si no existe (solo para KIKI, KAREN, DANIEL)
        res = um.validate_user_access(username)
        if not res or not res.get("exists"):
            if username == "RODOLFO":
                print(f"!!! Error: RODOLFO no existe en la nube. Saltando...")
                continue
            print(f">>> Registrando a {username}...")
            success, msg = um.add_new_user(username, "user", password)
            if not success:
                print(f"Error al registrar {username}: {msg}")
                continue
            print(f">>> Registro exitoso: {msg}")
        else:
            print(f">>> Usuario {username} ya existe.")
            
        # 2. Login/Activación para generar secretos
        try:
            print(f">>> Activando sesión para {username}...")
            # Si es RODOLFO y falla el password, intentaremos otros o saltaremos
            try:
                sm.set_active_user(username, password)
            except Exception as e:
                if username == "RODOLFO":
                    print(f"!!! No se pudo loguear como RODOLFO (Password incorrecto?). Saltando generacion de datos para el.")
                    continue
                else:
                    raise e
            
            # 3. Generar 100 secretos
            generate_random_secrets(sm, 100)
            
            # 4. Sincronizar
            print(f">>> Iniciando sincronización masiva para {username}...")
            sync_manager = SyncManager(sm, SUPABASE_URL, SUPABASE_KEY)
            stats = sync_manager.sync()
            print(f">>> Sincronización completada para {username}: {stats}")
            
        except Exception as e:
            print(f"Error procesando {username}: {e}")

if __name__ == "__main__":
    main()
