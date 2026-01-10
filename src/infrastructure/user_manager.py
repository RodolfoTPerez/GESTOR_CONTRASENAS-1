import pyotp
from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY
import base64, secrets   # ← faltaban

class UserManager:
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # ------------------------------------------------------------------
    #  TOTP – secreto fijo para debug (mismo que autenticador)
    # ------------------------------------------------------------------
    def get_or_create_totp_secret(self) -> str:
        # FORZAMOS el secreto que YA tienes en el autenticador
        return "JBSWY3DPEHPK3PXP"   # ← mismo que Google-Auth

    def verify_totp(self, secret: str, token: str) -> bool:
        try:
            totp = pyotp.TOTP(secret)
            # ✅ ventana más amplia para debug
            return totp.verify(token, valid_window=2)
        except Exception as e:
            print("Error TOTP:", e)
            return False


# ------------------------------------------------------------------
# Prueba rápida (solo si ejecutas este archivo directamente)
# ------------------------------------------------------------------
if __name__ == "__main__":
    import pyotp, time
    secret = "JBSWY3DPEHPK3PXP"
    while True:
        tok = pyotp.TOTP(secret).now()
        print(tok, "  (Quedan:", int(30 - time.time() % 30), "s)", end="\r")
        time.sleep(1)