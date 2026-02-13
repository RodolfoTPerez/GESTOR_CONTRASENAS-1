from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

try:
    # No hay una forma directa de ver políticas vía API rest de Supabase fácilmente 
    # sin llamar a una función rpc. Pero podemos intentar ver si 'secrets' tiene RLS habilitado.
    # Intentaremos listar tablas y sus propiedades si es posible.
    
    # Probemos una consulta simple para ver si falla por RLS o algo
    res = supabase.table("secrets").select("count").execute()
    print(f"Respuesta de secrets count: {res}")
    
except Exception as e:
    print(f"Error: {e}")
