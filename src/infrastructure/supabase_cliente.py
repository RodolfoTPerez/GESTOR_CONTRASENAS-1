import os
from supabase import create_client

# Variables de entorno
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


class SupabaseClient:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError("Faltan SUPABASE_URL o SUPABASE_KEY en el entorno.")

        self.client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # ---------------------------------------------------------
    # OBTENER TODOS LOS SECRETOS
    # ---------------------------------------------------------
    def fetch_all_secrets(self):
        """
        Devuelve todos los registros de la tabla 'secrets'.
        """
        response = self.client.table("secrets").select("*").execute()
        return response.data or []

    # ---------------------------------------------------------
    # BORRAR TODO (NO SE USA EN SINCRONIZACIÓN REAL)
    # ---------------------------------------------------------
    def clear_secrets(self):
        """
        Borra todos los registros de la tabla.
        No se usa en sincronización bidireccional.
        """
        self.client.table("secrets").delete().gt("id", 0).execute()

    # ---------------------------------------------------------
    # INSERTAR NUEVO REGISTRO
    # ---------------------------------------------------------
    def insert_secret(self, record: dict):
        """
        Inserta un nuevo registro en Supabase.
        Devuelve el registro insertado con su ID.
        """
        response = self.client.table("secrets").insert(record).execute()
        return response.data[0] if response.data else None

    # ---------------------------------------------------------
    # ACTUALIZAR REGISTRO EXISTENTE
    # ---------------------------------------------------------
    def update_secret(self, remote_id, record: dict):
        """
        Actualiza un registro existente en Supabase usando su ID.
        """
        response = (
            self.client
            .table("secrets")
            .update(record)
            .eq("id", remote_id)
            .execute()
        )
        return response.data[0] if response.data else None
