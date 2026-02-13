"""
Verificar servicios en Supabase
================================
"""
import os
from supabase import create_client

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)
    
    # Obtener todos los servicios
    response = supabase.table("secrets").select("id, service, owner_name, is_private").execute()
    
    print("=" * 80)
    print("SERVICIOS EN SUPABASE")
    print("=" * 80)
    print(f"{'ID':<5} | {'SERVICIO':<20} | {'OWNER':<15} | {'PRIVADO':<10}")
    print("-" * 80)
    
    public_count = 0
    private_count = 0
    
    for s in response.data:
        sid = s.get('id', 'N/A')
        service = s.get('service', 'N/A')
        owner = s.get('owner_name', 'NULL')
        is_private = s.get('is_private', 0)
        
        privacy = "PRIVADO" if is_private == 1 else "PUBLICO"
        
        if is_private == 1:
            private_count += 1
        else:
            public_count += 1
        
        print(f"{sid:<5} | {service:<20} | {owner:<15} | {privacy:<10}")
    
    print("-" * 80)
    print(f"Total: {len(response.data)} servicios ({public_count} públicos, {private_count} privados)")
    print("=" * 80)
else:
    print("[ERROR] Variables SUPABASE_URL o SUPABASE_KEY no configuradas")
