from pathlib import Path
import os
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv(str(BASE_DIR) + "/.env")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

def ver_politicas_rls():
    sb = create_client(url, key)
    
    query = """
    SELECT 
        schemaname, 
        tablename, 
        policyname, 
        permissive, 
        roles, 
        cmd, 
        qual, 
        with_check 
    FROM pg_policies 
    WHERE tablename = 'secrets';
    """
    
    try:
        print("Consultando políticas RLS para 'secrets'...")
        # Intentamos usar la función rpc 'exec_sql' si existe
        res = sb.rpc('exec_sql', {'query': query}).execute()
        if res.data:
            for p in res.data:
                print(f"\nPolítica: {p['policyname']}")
                print(f"  Comando: {p['cmd']}")
                print(f"  Check: {p['with_check']}")
                print(f"  Qual: {p['qual']}")
        else:
            print("No se encontraron políticas o no tienes permisos para verlas vía RPC.")
    except Exception as e:
        print(f"Error consultando políticas: {e}")
        print("\nSugerencia: Ejecuta 'SELECT * FROM pg_policies WHERE tablename = 'secrets';' en el SQL Editor de Supabase.")

if __name__ == "__main__":
    ver_politicas_rls()
