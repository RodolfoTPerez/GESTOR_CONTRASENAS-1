import os
import sys
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def ver_columnas():
    # El truco para ver columnas sin registros usando un filtro inexistente
    # y revisando si el error nos da pistas o usando rpc si existiera
    # Pero lo mejor es intentar un insert vacio para que nos diga que falta
    tablas = ["users", "vaults", "vault_groups", "secrets"]
    for t in tablas:
        print(f"\nTABLA: {t}")
        try:
            # Insertamos un registro vacio o con campos absurdos para disparar el mensaje de error de Postgres
            # que lista las columnas requeridas o fallos de tipo.
            res = supabase.table(t).insert({}).execute()
        except Exception as e:
            print(f"Estructura: {e}")

if __name__ == "__main__":
    ver_columnas()
