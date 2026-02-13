"""
Script de Diagnóstico 2FA
Verifica el estado del secreto TOTP en Supabase y SQLite
"""
import os
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY
import sqlite3

def diagnosticar_2fa(username="RODOLFO"):
    print(f"\n{'='*60}")
    print(f"DIAGNOSTICO 2FA PARA: {username}")
    print(f"{'='*60}\n")
    
    # 1. Verificar Supabase
    print("1. VERIFICANDO SUPABASE...")
    try:
        sb = create_client(SUPABASE_URL, SUPABASE_KEY)
        resp = sb.table("users").select("username,totp_secret").eq("username", username).execute()
        
        if resp.data:
            user = resp.data[0]
            secret = user.get("totp_secret")
            print(f"   [OK] Usuario encontrado en Supabase")
            print(f"   Secreto: {secret[:20]}... (primeros 20 chars)")
            print(f"   Longitud: {len(secret) if secret else 0} caracteres")
            print(f"   Tipo: {'Base32 (texto plano)' if secret and len(secret) < 40 else 'Base64 (cifrado)'}")
        else:
            print(f"   [ERROR] Usuario NO encontrado en Supabase")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    # 2. Verificar SQLite Local
    print(f"\n2. VERIFICANDO SQLITE LOCAL...")
    db_path = Path(__file__).parent / "data" / f"vault_{username.lower()}.db"
    
    if not db_path.exists():
        print(f"   [ERROR] Base de datos local NO existe: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT totp_secret FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0]:
            secret = row[0]
            print(f"   [OK] Secreto encontrado en SQLite")
            print(f"   Valor: {str(secret)[:20] if len(str(secret)) > 20 else secret}...")
            print(f"   Tipo Python: {type(secret)}")
            print(f"   Longitud: {len(str(secret))} caracteres")
        else:
            print(f"   [ERROR] Secreto NO encontrado en SQLite")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    # 3. Test de Cifrado/Descifrado
    print(f"\n3. TEST DE CIFRADO/DESCIFRADO...")
    try:
        from config.config import TOTP_SYSTEM_KEY
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        import hashlib
        import base64
        import secrets as sec
        
        test_secret = "JBSWY3DPEHPK3PXP"  # Secreto de prueba
        
        # Cifrar
        key = hashlib.sha256(TOTP_SYSTEM_KEY.encode()).digest()
        cipher = AESGCM(key)
        nonce = sec.token_bytes(12)
        encrypted = cipher.encrypt(nonce, test_secret.encode('utf-8'), None)
        payload = base64.b64encode(nonce + encrypted).decode('ascii')
        
        print(f"   [OK] Cifrado exitoso")
        print(f"   Secreto original: {test_secret}")
        print(f"   Cifrado: {payload[:40]}...")
        
        # Descifrar
        decoded = base64.b64decode(payload)
        nonce2 = decoded[:12]
        ciphertext = decoded[12:]
        decrypted = cipher.decrypt(nonce2, ciphertext, None)
        result = decrypted.decode('utf-8')
        
        print(f"   [OK] Descifrado exitoso")
        print(f"   Resultado: {result}")
        print(f"   Coincide: {'SI' if result == test_secret else 'NO'}")
        
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    diagnosticar_2fa()
