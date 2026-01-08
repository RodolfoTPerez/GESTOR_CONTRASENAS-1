from PySide6.QtWidgets import QApplication
 

from src.presentation.login_view import LoginView
from src.presentation.dashboard_view import DashboardView


def start_app():
    app = QApplication([])

    # Función que se ejecuta tras login exitoso
    def on_login_success(master_password):
        dashboard = DashboardView(master_password)
        dashboard.show()

    login_window = LoginView(on_login_success)
    login_window.show()

    app.exec()

if __name__ == "__main__":
    start_app()
