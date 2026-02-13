import os
import sys
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def ver_columnas_users():
    print("\nTABLA: users")
    try:
        # Forzar error en users para ver campos (enviando algo que no sea null para id pero faltando el resto)
        # Probamos enviando un username repetido o algo que active el esquema
        res = supabase.table("users").insert({"id": 9999}).execute()
    except Exception as e:
        print(f"Estructura: {e}")

if __name__ == "__main__":
    ver_columnas_users()
