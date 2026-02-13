"""
Debug de sync_user_to_local para ver por que protected_key no se guarda
"""
from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY
import base64

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Obtener datos de Supabase
user_res = supabase.table("users").select("*").eq("username", "RODOLFO").execute()

if user_res.data:
    cloud_profile = user_res.data[0]
    
    print("=" * 80)
    print("DEBUG: DECODIFICACION DE PROTECTED_KEY")
    print("=" * 80)
    
    protected_key_b64 = cloud_profile.get("protected_key")
    
    print(f"\n[1] VALOR RAW DESDE SUPABASE:")
    print(f"   Type: {type(protected_key_b64)}")
    print(f"   Length: {len(protected_key_b64) if protected_key_b64 else 0}")
    print(f"   Value: {protected_key_b64[:100] if protected_key_b64 else 'NULL'}")
    
    if protected_key_b64:
        print(f"\n[2] INTENTANDO DECODIFICAR...")
        
        # Logica actual de sync_user_to_local
        if isinstance(protected_key_b64, str) and protected_key_b64.startswith("\\x"):
            print(f"   [INFO] Detectado formato \\x")
            try:
                # Paso 1: Hex → ASCII (Base64)
                ascii_b64 = bytes.fromhex(protected_key_b64[2:]).decode('ascii')
                print(f"   [OK] Paso 1 (Hex -> ASCII): {ascii_b64[:50]}")
                
                # Paso 2: Base64 → Bytes
                protected_key_bytes = base64.b64decode(ascii_b64)
                print(f"   [OK] Paso 2 (Base64 -> Bytes): {len(protected_key_bytes)} bytes")
                print(f"   [OK] Primeros 16 bytes (hex): {protected_key_bytes[:16].hex()}")
                
                print(f"\n[3] RESULTADO FINAL:")
                print(f"   protected_key_bytes = {protected_key_bytes is not None}")
                print(f"   Type: {type(protected_key_bytes)}")
                print(f"   Length: {len(protected_key_bytes)}")
                
            except Exception as e:
                print(f"   [ERROR] Fallo en decodificacion: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"   [WARN] No tiene prefijo \\x")
    else:
        print(f"\n[ERROR] protected_key es None en Supabase")
    
    print("\n" + "=" * 80)
