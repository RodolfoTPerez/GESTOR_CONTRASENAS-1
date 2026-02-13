"""
Script para ver el esquema completo de Supabase
Muestra todas las tablas y sus relaciones
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY

def ver_esquema():
    print(f"\n{'='*80}")
    print("ESQUEMA COMPLETO DE SUPABASE")
    print(f"{'='*80}\n")
    
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 1. Listar todas las tablas en el esquema public
    print("1. TABLAS EN EL ESQUEMA PUBLIC:")
    print("-" * 80)
    
    query = """
    SELECT 
        table_name,
        (SELECT COUNT(*) FROM information_schema.columns 
         WHERE table_name = t.table_name AND table_schema = 'public') as num_columnas
    FROM information_schema.tables t
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    ORDER BY table_name;
    """
    
    try:
        result = sb.rpc('exec_sql', {'query': query}).execute()
        if result.data:
            for row in result.data:
                print(f"  - {row['table_name']:30} ({row['num_columnas']} columnas)")
    except:
        # Método alternativo si RPC no funciona
        print("  [Método directo - listado básico]")
        tablas = [
            'users', 'vaults', 'secrets', 'vault_access', 
            'vault_groups', 'invitations', 'security_audit',
            'totp', 'master'
        ]
        for tabla in tablas:
            try:
                resp = sb.table(tabla).select("*", count='exact').limit(0).execute()
                print(f"  - {tabla:30} (existe)")
            except Exception as e:
                if "does not exist" in str(e).lower():
                    print(f"  - {tabla:30} (NO EXISTE)")
    
    # 2. Ver cantidad de registros en cada tabla
    print(f"\n2. CANTIDAD DE REGISTROS:")
    print("-" * 80)
    
    tablas_conocidas = [
        'users', 'vaults', 'secrets', 'vault_access', 
        'vault_groups', 'invitations', 'security_audit',
        'totp', 'master'
    ]
    
    for tabla in tablas_conocidas:
        try:
            resp = sb.table(tabla).select("*", count='exact').limit(0).execute()
            count = resp.count if hasattr(resp, 'count') else 0
            print(f"  {tabla:30} = {count} registros")
        except Exception as e:
            if "does not exist" not in str(e).lower():
                print(f"  {tabla:30} = ERROR: {str(e)[:50]}")
    
    # 3. Ver estructura de tablas clave
    print(f"\n3. ESTRUCTURA DE TABLAS DESCONOCIDAS:")
    print("-" * 80)
    
    for tabla in ['vault_groups', 'totp', 'master']:
        print(f"\nTabla: {tabla}")
        try:
            # Intentar obtener columnas
            resp = sb.table(tabla).select("*").limit(1).execute()
            if resp.data and len(resp.data) > 0:
                print(f"  Columnas: {', '.join(resp.data[0].keys())}")
                print(f"  Ejemplo: {resp.data[0]}")
            else:
                print(f"  (Tabla existe pero está vacía)")
        except Exception as e:
            if "does not exist" in str(e).lower():
                print(f"  [NO EXISTE]")
            else:
                print(f"  Error: {e}")
    
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    ver_esquema()
