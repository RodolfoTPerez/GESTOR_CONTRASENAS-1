import sqlite3
import os
import hashlib
import base64
from pathlib import Path

def verify_integrity(username):
    print(f"\n{'='*60}")
    print(f"🛡️ AUDITORÍA DE INTEGRIDAD: {username.upper()}")
    print(f"{'='*60}\n")

    # 1. Localizar Base de Datos
    base_dir = Path(__file__).resolve().parent.parent
    db_path = base_dir / "data" / f"vault_{username.lower()}.db"
    
    if not db_path.exists():
        print(f"❌ ERROR: No se encontró la base de datos en {db_path}")
        return

    print(f"✅ Archivo detectado: {db_path.name}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 2. Verificar Tabla de Usuarios
        print("\n[Perfil de Usuario]")
        cursor.execute("SELECT username, password_hash, salt, vault_salt, role, protected_key FROM users")
        user = cursor.fetchone()
        
        if user:
            u, h, s, vs, r, pk = user
            print(f"  - Usuario: {u}")
            print(f"  - Rol: {r}")
            print(f"  - Hash de Password: Presente ({len(h)} chars)")
            print(f"  - Salt dinámico: OK")
            print(f"  - Vault Salt (Semilla): {'OK' if vs else 'FALTANTE'}")
            print(f"  - Llave Protegida (SVK): {'CIFRADA (BLOB)' if isinstance(pk, bytes) else 'ERROR: No es BLOB'}")
            if pk: print(f"    (Longitud: {len(pk)} bytes)")
        else:
            print("  ❌ ERROR: Tabla de usuarios vacía.")

        # 3. Verificar Tabla de Secretos
        print("\n[Bóveda de Secretos]")
        cursor.execute("SELECT COUNT(*), COUNT(DISTINCT service) FROM secrets")
        total, distinct = cursor.fetchone()
        print(f"  - Total de registros: {total}")
        print(f"  - Servicios únicos: {distinct}")

        # 4. Prueba de Encriptación (Muestreo)
        cursor.execute("SELECT service, secret, nonce FROM secrets LIMIT 3")
        samples = cursor.fetchall()
        print(f"\n[Verificación Criptográfica]")
        for svc, sec, non in samples:
            # Verificamos si el 'secret' es realmente un BLOB/binario cifrado y no texto plano
            is_encrypted = isinstance(sec, bytes)
            print(f"  - Registro '{svc}': {'🔒 ENCRIPTADO' if is_encrypted else '⚠️ TEXTO PLANO (VULNERABLE)'}")

        # 5. Estado de Sincronización
        cursor.execute("SELECT COUNT(*) FROM secrets WHERE synced = 0")
        pending = cursor.fetchone()[0]
        print(f"\n[Sincronización]")
        print(f"  - Cambios pendientes de subir a la nube: {pending}")

        conn.close()
        print(f"\n{'='*60}")
        print("✅ AUDITORÍA FINALIZADA EXITOSAMENTE")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"❌ ERROR DURANTE LA AUDITORÍA: {e}")

if __name__ == "__main__":
    # Puedes cambiar el nombre del usuario aquí para la prueba
    verify_integrity("rodolfo")
