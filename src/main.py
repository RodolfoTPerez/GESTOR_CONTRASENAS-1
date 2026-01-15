import sys
from PyQt5.QtWidgets import QApplication, QMessageBox

from src.presentation.login_view import LoginView
from src.presentation.dashboard_view import DashboardView
from src.infrastructure.secrets_manager import SecretsManager
from src.infrastructure.sync_manager import SyncManager
from src.infrastructure.user_manager import UserManager
from config.config import SUPABASE_URL, SUPABASE_KEY


def start_app():
    app = QApplication(sys.argv)

    # Creamos el login primero
    login_window = LoginView(None)

    # Definimos el callback AHORA que login_window existe
    def on_login_success(master_password, totp_secret):
        print(">>> on_login_success ejecutado")
        try:
            sm = SecretsManager(master_password)
            print(">>> SecretsManager creado")

            um = UserManager()
            print(">>> UserManager creado")

            sync = SyncManager(sm, SUPABASE_URL, SUPABASE_KEY)
            print(">>> SyncManager creado")

            # ⭐ REFERENCIA PERSISTENTE AQUÍ
            login_window.dashboard = DashboardView(sm, sync, um)
            print(">>> DashboardView creado")

            login_window.dashboard.show()
            print(">>> Dashboard mostrado")

        except Exception as e:
            print(">>> ERROR en on_login_success:", repr(e))
            QMessageBox.critical(
                None,
                "Error crítico",
                f"Fallo al crear el dashboard:\n{e}"
            )

    # Ahora que existe el callback, lo asignamos
    login_window.on_login_success = on_login_success

    login_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    start_app()
