#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMPARAR DATOS: RODOLFO vs KIKI
================================

Compara qué diferencias hay entre los datos de ambos usuarios.
"""

import sys
import sqlite3
from pathlib import Path

print("="*70)
print("🔍 COMPARACIÓN: RODOLFO vs KIKI")
print("="*70)
print()

# Función para analizar usuario
def analyze_user(username):
    db_path = Path(f"data/vault_{username.lower()}.db")
    
    if not db_path.exists():
        return None
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Obtener columnas de la tabla secrets
    cursor.execute("PRAGMA table_info(secrets)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Contar secretos
    cursor.execute("SELECT COUNT(*) FROM secrets")
    total_secrets = cursor.fetchone()[0]
    
    # Ver si tienen columna version
    has_version = 'version' in columns
    
    # Si tiene version, ver cuántos tienen valor
    version_count = 0
    if has_version:
        cursor.execute("SELECT COUNT(*) FROM secrets WHERE version IS NOT NULL AND version != ''")
        version_count = cursor.fetchone()[0]
    
    # Ver un secreto de ejemplo
    cursor.execute("SELECT * FROM secrets LIMIT 1")
    sample_secret = cursor.fetchone()
    
    conn.close()
    
    return {
        'username': username,
        'columns': columns,
        'has_version': has_version,
        'total_secrets': total_secrets,
        'version_count': version_count,
        'sample_secret': sample_secret
    }

# Analizar RODOLFO
print("👤 Analizando RODOLFO...")
rodolfo = analyze_user("RODOLFO")

if rodolfo:
    print(f"✅ Base de datos encontrada")
    print(f"   Total secretos: {rodolfo['total_secrets']}")
    print(f"   Tiene columna 'version': {rodolfo['has_version']}")
    if rodolfo['has_version']:
        print(f"   Secretos con version: {rodolfo['version_count']}")
    print(f"   Columnas totales: {len(rodolfo['columns'])}")
else:
    print("❌ No se encontró base de datos")

print()

# Analizar KIKI
print("👤 Analizando KIKI...")
kiki = analyze_user("KIKI")

if kiki:
    print(f"✅ Base de datos encontrada")
    print(f"   Total secretos: {kiki['total_secrets']}")
    print(f"   Tiene columna 'version': {kiki['has_version']}")
    if kiki['has_version']:
        print(f"   Secretos con version: {kiki['version_count']}")
    print(f"   Columnas totales: {len(kiki['columns'])}")
else:
    print("❌ No se encontró base de datos")

print()
print("="*70)
print("📊 COMPARACIÓN")
print("="*70)
print()

if rodolfo and kiki:
    # Comparar columnas
    print("🔍 Diferencias en columnas:")
    
    rodolfo_cols = set(rodolfo['columns'])
    kiki_cols = set(kiki['columns'])
    
    only_rodolfo = rodolfo_cols - kiki_cols
    only_kiki = kiki_cols - rodolfo_cols
    
    if only_rodolfo:
        print(f"  Solo RODOLFO tiene: {', '.join(only_rodolfo)}")
    
    if only_kiki:
        print(f"  Solo KIKI tiene: {', '.join(only_kiki)}")
    
    if not only_rodolfo and not only_kiki:
        print("  ✅ Ambos tienen las mismas columnas")
    
    print()
    
    # Comparar secretos
    print("📊 Comparación de datos:")
    print(f"  RODOLFO: {rodolfo['total_secrets']} secretos")
    print(f"  KIKI: {kiki['total_secrets']} secretos")
    
    if rodolfo['has_version'] and kiki['has_version']:
        print()
        print(f"  RODOLFO con 'version': {rodolfo['version_count']}/{rodolfo['total_secrets']}")
        print(f"  KIKI con 'version': {kiki['version_count']}/{kiki['total_secrets']}")
    
    print()
    
    # Conclusión
    print("="*70)
    print("💡 EXPLICACIÓN DEL PROBLEMA")
    print("="*70)
    print()
    
    if rodolfo['version_count'] == 0 and kiki['version_count'] > 0:
        print("🎯 PROBLEMA IDENTIFICADO:")
        print()
        print("  Los secretos de RODOLFO NO tienen valores en 'version',")
        print("  pero los secretos de KIKI SÍ tienen.")
        print()
        print("  Cuando KIKI intenta sincronizar, envía el campo 'version'")
        print("  a Supabase, pero Supabase no tiene esa columna.")
        print()
        print("  RODOLFO no tiene el problema porque sus secretos")
        print("  tienen 'version' = NULL o vacío, entonces NO se envía.")
        print()
    elif rodolfo['total_secrets'] == 0:
        print("🎯 PROBLEMA IDENTIFICADO:")
        print()
        print("  RODOLFO no tiene secretos para sincronizar,")
        print("  por eso no falla el sync.")
        print()
        print("  KIKI tiene secretos con el campo 'version',")
        print("  y al intentar sincronizarlos, Supabase rechaza")
        print("  porque no tiene esa columna.")
        print()
    else:
        print("🔍 Ambos usuarios tienen estructura similar.")
        print("   El problema podría ser otro.")
    
    print("✅ SOLUCIÓN:")
    print()
    print("  Agregar la columna 'version' en Supabase:")
    print()
    print("  ALTER TABLE secrets ADD COLUMN version TEXT;")
    print()

else:
    print("⚠️  No se pudieron comparar ambos usuarios")

print("="*70)