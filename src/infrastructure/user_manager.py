import pyotp
from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY


class UserManager:
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    def get_or_create_totp_secret(self) -> str:
        # Obtener el primer (y único) TOTP
        resp = (
            self.supabase
            .table("totp")
            .select("secret")
            .limit(1)
            .execute()
        )

        if resp.data:
            return resp.data[0]["secret"]

        # Crear nuevo secreto
        secret = pyotp.random_base32()

        self.supabase.table("totp").insert({
            "secret": secret
        }).execute()

        return secret

    def verify_totp(self, secret: str, token: str) -> bool:
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=1)
        except Exception as e:
            print("Error TOTP:", e)
            return False
