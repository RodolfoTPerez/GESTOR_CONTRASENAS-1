import base64
from pathlib import Path
from supabase import create_client, Client
from datetime import datetime
from .secrets_manager import SecretsManager
from dotenv import load_dotenv
import os

# ===============================
# CARGA DE VARIABLES DE ENTORNO
# ===============================
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError("Variables SUPABASE_URL y SUPABASE_KEY no definidas en .env")

# ===============================
# CLIENTE SUPABASE
# ===============================
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ===============================
# CLASE DE SINCRONIZACIÓN
# ===============================
class SupabaseSync:
    def __init__(self, secrets_manager: SecretsManager):
        self.manager = secrets_manager

    # -------------------------------
    # SUBIR SECRETOS A SUPABASE
    # -------------------------------
    def push_secret(self, secret_id: str):
        """
        Sube un secret específico a Supabase.
        """
        # Obtener secret de SQLite
        conn_secret = self.manager.get_secret(secret_id)
        # NOTA: El secret ya está cifrado internamente, solo convertimos a base64 para transporte
        ciphertext, nonce = self.manager.encrypt_secret(conn_secret)
        ciphertext_b64 = base64.b64encode(ciphertext).decode()
        nonce_b64 = base64.b64encode(nonce).decode()

        # Preparar payload
        row = next((s for s in self.manager.list_secrets() if s["id"] == secret_id), None)
        if not row:
            raise ValueError("Secret no encontrado")

        data = {
            "id": secret_id,
            "service": row["service"],
            "user": row["user"],
            "secret": ciphertext_b64,
            "nonce": nonce_b64,
            "created_at": datetime.utcnow().isoformat(),
        }

        # Insertar o actualizar
        response = supabase.table("secrets").upsert(data).execute()
        if response.error:
            raise Exception(f"Error al subir a Supabase: {response.error}")
        return response.data

    # -------------------------------
    # DESCARGAR SECRETOS DE SUPABASE
    # -------------------------------
    def pull_secrets(self):
        """
        Trae todos los secrets de Supabase y los guarda en SQLite local.
        """
        response = supabase.table("secrets").select("*").execute()
        if response.error:
            raise Exception(f"Error al obtener secrets: {response.error}")

        for row in response.data:
            secret_id = row["id"]
            service = row["service"]
            user = row["user"]
            ciphertext = base64.b64decode(row["secret"])
            nonce = base64.b64decode(row["nonce"])

            # Desencriptamos con clave maestra
            plaintext = self.manager.decrypt_secret(self.manager.key, ciphertext, nonce)

            # Guardar en SQLite
            try:
                self.manager.create_secret(service, user, plaintext)
            except Exception:
                # Si ya existe, actualizar
                secrets_list = self.manager.list_secrets()
                if any(s["id"] == secret_id for s in secrets_list):
                    self.manager.update_secret(secret_id, plaintext)

    # -------------------------------
    # SINCRONIZACIÓN COMPLETA
    # -------------------------------
    def sync_all(self):
        """
        Sincroniza todos los secretos bidireccionalmente.
        Estrategia simple: pull -> merge local -> push.
        """
        self.pull_secrets()
        for secret in self.manager.list_secrets():
            self.push_secret(secret["id"])

