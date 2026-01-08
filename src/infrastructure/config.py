# src/infrastructure/config.py
from dotenv import load_dotenv
import os

# Cargar variables de .env ubicado en C:\PassGuardian\.env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

