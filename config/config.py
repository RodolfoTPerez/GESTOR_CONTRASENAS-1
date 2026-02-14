import os
from dotenv import load_dotenv
from src.infrastructure.config.path_manager import PathManager

load_dotenv(PathManager.ENV_FILE)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# System Key (Pepper) para cifrado de secretos 2FA
# Esta clave rompe el bucle circular: no depende de la contraseña del usuario
# pero protege los secretos en la base de datos
TOTP_SYSTEM_KEY = os.getenv("TOTP_SYSTEM_KEY")

required_vars = ["SUPABASE_URL", "SUPABASE_KEY"]
missing = [var for var in required_vars if not os.getenv(var)]

if missing:
    raise EnvironmentError(
        f"Variables de entorno faltantes: {', '.join(missing)}\n"
        f"Copie .env.example a .env y configure las credenciales."
    )

# Validación de seguridad: No permitir valores por defecto en producción
if "your-project-id" in os.getenv("SUPABASE_URL", ""):
     raise ValueError("Configure SUPABASE_URL con su proyecto real en .env")

# --- SENIOR SECURITY: DEBUG PROTECTION (Kill Switch) ---
DEBUG_MODE = os.getenv("DEBUG", "False").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()

if DEBUG_MODE and ENVIRONMENT == "production":
    raise RuntimeError(
        "CRITICAL SECURITY RISK: DEBUG=True is enabled in a PRODUCTION environment. "
        "The application will not start until DEBUG is set to False in your .env file."
    )
