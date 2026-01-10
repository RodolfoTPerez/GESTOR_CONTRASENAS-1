import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from PySide6.QtWidgets import QApplication
from src.presentation.login_view import LoginView
from src.presentation.dashboard_view import DashboardView


def on_login_success(master_password: str):
    # ✅ Crear SecretsManager antes de pasar
    from src.infrastructure.secrets_manager import SecretsManager
    sm = SecretsManager(master_password)
    dashboard = DashboardView(sm)
    dashboard.show()


def start_app():
    app = QApplication([])
    login_window = LoginView(on_login_success)
    login_window.show()
    app.exec()


if __name__ == "__main__":
    start_app()