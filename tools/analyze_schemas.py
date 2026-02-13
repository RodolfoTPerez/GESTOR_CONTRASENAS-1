from pathlib import Path
import os
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
"""
Analisis comparativo de esquemas: Supabase vs SQLite
Verifica que las tablas y campos esten alineados correctamente
"""
from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY
import sqlite3
from pathlib import Path
import sys

# Fix encoding for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("ANALISIS DE ESQUEMAS: SUPABASE vs SQLITE")
print("=" * 80)

# PARTE 1: ESQUEMA DE SUPABASE
print("\n[1] CONSULTANDO ESQUEMA DE SUPABASE...")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    user_res = supabase.table("users").select("*").eq("username", "RODOLFO").execute()
    if user_res.data:
        supabase_user = user_res.data[0]
        print("\n[SUPABASE] TABLA 'users':")
        print(f"   Campos encontrados: {len(supabase_user)}")
        for key, value in supabase_user.items():
            value_type = type(value).__name__
            value_len = len(value) if isinstance(value, (str, bytes, list, dict)) else "N/A"
            value_preview = str(value)[:50] if value else "NULL"
            print(f"   - {key:20s} | Type: {value_type:10s} | Len: {str(value_len):6s} | Preview: {value_preview}")
    else:
        print("   [WARN] No se encontro el usuario RODOLFO")
except Exception as e:
    print(f"   [ERROR] {e}")

# Verificar vault_access
try:
    user_id = supabase_user.get('id') if user_res.data else None
    vault_id = supabase_user.get('vault_id') if user_res.data else None
    
    if user_id and vault_id:
        va_res = supabase.table("vault_access").select("*").eq("user_id", user_id).eq("vault_id", vault_id).execute()
        if va_res.data:
            supabase_va = va_res.data[0]
            print("\n[SUPABASE] TABLA 'vault_access':")
            print(f"   Campos encontrados: {len(supabase_va)}")
            for key, value in supabase_va.items():
                value_type = type(value).__name__
                value_len = len(value) if isinstance(value, (str, bytes, list, dict)) else "N/A"
                value_preview = str(value)[:50] if value else "NULL"
                print(f"   - {key:20s} | Type: {value_type:10s} | Len: {str(value_len):6s} | Preview: {value_preview}")
except Exception as e:
    print(f"   [WARN] No se pudo consultar vault_access: {e}")

# PARTE 2: ESQUEMA DE SQLITE LOCAL
print("\n[2] CONSULTANDO ESQUEMA DE SQLITE LOCAL...")
db_path = Path(str(BASE_DIR) + "/data/vault_rodolfo.db")

if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Obtener esquema de la tabla users
    cursor.execute("PRAGMA table_info(users)")
    sqlite_schema = cursor.fetchall()
    
    print("\n[SQLITE] TABLA 'users' (ESQUEMA):")
    print(f"   Campos definidos: {len(sqlite_schema)}")
    for col in sqlite_schema:
        col_id, name, col_type, not_null, default, pk = col
        print(f"   - {name:20s} | Type: {col_type:10s} | NotNull: {not_null} | PK: {pk}")
    
    # Obtener datos reales
    cursor.execute("SELECT * FROM users WHERE username = 'RODOLFO'")
    row = cursor.fetchone()
    
    if row:
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        print("\n[SQLITE] TABLA 'users' (DATOS REALES):")
        for i, col_name in enumerate(columns):
            value = row[i]
            value_type = type(value).__name__
            value_len = len(value) if isinstance(value, (str, bytes)) else "N/A"
            value_preview = str(value)[:50] if value else "NULL"
            if isinstance(value, bytes):
                value_preview = value[:16].hex() + "..." if len(value) > 16 else value.hex()
            print(f"   - {col_name:20s} | Type: {value_type:10s} | Len: {str(value_len):6s} | Preview: {value_preview}")
    else:
        print("   [WARN] No se encontro el usuario RODOLFO en SQLite")
    
    conn.close()
else:
    print(f"   [ERROR] No existe la base de datos: {db_path}")

# PARTE 3: COMPARACION Y ANALISIS
print("\n" + "=" * 80)
print("ANALISIS DE DISCREPANCIAS")
print("=" * 80)

if user_res.data and row:
    print("\n[COMPARANDO CAMPOS CRITICOS]")
    
    # Comparar protected_key
    supabase_pk = supabase_user.get('protected_key')
    sqlite_pk = row[columns.index('protected_key')] if 'protected_key' in columns else None
    
    print(f"\n1. PROTECTED_KEY:")
    print(f"   Supabase: Type={type(supabase_pk).__name__}, Len={len(supabase_pk) if supabase_pk else 0}")
    if isinstance(supabase_pk, str):
        print(f"   Supabase Preview: {supabase_pk[:50]}")
    print(f"   SQLite:   Type={type(sqlite_pk).__name__}, Len={len(sqlite_pk) if sqlite_pk else 0}")
    if isinstance(sqlite_pk, bytes):
        print(f"   SQLite Preview (hex): {sqlite_pk[:16].hex()}")
    
    # Comparar wrapped_vault_key
    supabase_wvk = supabase_user.get('wrapped_vault_key')
    sqlite_wvk = row[columns.index('wrapped_vault_key')] if 'wrapped_vault_key' in columns else None
    
    print(f"\n2. WRAPPED_VAULT_KEY (desde tabla users):")
    print(f"   Supabase: Type={type(supabase_wvk).__name__}, Len={len(supabase_wvk) if supabase_wvk else 0}")
    if isinstance(supabase_wvk, str) and supabase_wvk:
        print(f"   Supabase Preview: {supabase_wvk[:50]}")
    print(f"   SQLite:   Type={type(sqlite_wvk).__name__}, Len={len(sqlite_wvk) if sqlite_wvk else 0}")
    if isinstance(sqlite_wvk, bytes) and sqlite_wvk:
        print(f"   SQLite Preview (hex): {sqlite_wvk[:16].hex()}")
    
    # Comparar wrapped_master_key de vault_access
    if va_res.data:
        supabase_wmk = supabase_va.get('wrapped_master_key')
        print(f"\n3. WRAPPED_MASTER_KEY (desde tabla vault_access):")
        print(f"   Supabase: Type={type(supabase_wmk).__name__}, Len={len(supabase_wmk) if supabase_wmk else 0}")
        if isinstance(supabase_wmk, str):
            print(f"   Supabase Preview: {supabase_wmk[:50]}")
            print(f"   Supabase es HEX puro: {all(c in '0123456789abcdefABCDEF' for c in supabase_wmk)}")
    
    # Comparar vault_salt
    supabase_vs = supabase_user.get('vault_salt')
    sqlite_vs = row[columns.index('vault_salt')] if 'vault_salt' in columns else None
    
    print(f"\n4. VAULT_SALT:")
    print(f"   Supabase: Type={type(supabase_vs).__name__}, Len={len(supabase_vs) if supabase_vs else 0}")
    if isinstance(supabase_vs, str):
        print(f"   Supabase Preview: {supabase_vs[:50]}")
    print(f"   SQLite:   Type={type(sqlite_vs).__name__}, Len={len(sqlite_vs) if sqlite_vs else 0}")
    if isinstance(sqlite_vs, bytes):
        print(f"   SQLite Preview (hex): {sqlite_vs[:16].hex()}")

print("\n" + "=" * 80)
print("ANALISIS COMPLETADO")
print("=" * 80)
