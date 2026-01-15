import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QTableWidget, QTableWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt
from infrastructure.security import verify_totp
from infrastructure.secrets_manager import SecretsManager
from infrastructure.supabase_sync import SupabaseSync

# ===============================
# CONFIG
# ===============================
MASTER_PASSWORD = "MiClaveMaestra123!"  # En la práctica, ingresar por login
TOTP_SECRET = "JBSWY3DPEHPK3PXP"       # Reemplazar con secreto real o cargar de DB

# ===============================
# LOGIN WINDOW
# ===============================
class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PassGuardian Login")
        self.setFixedSize(400, 200)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Clave maestra
        self.master_label = QLabel("Clave Maestra:")
        self.master_input = QLineEdit()
        self.master_input.setEchoMode(QLineEdit.Password)

        # Token 2FA
        self.totp_label = QLabel("Token 2FA:")
        self.totp_input = QLineEdit()

        # Botón Login
        self.login_btn = QPushButton("Iniciar sesión")
        self.login_btn.clicked.connect(self.handle_login)

        layout.addWidget(self.master_label)
        layout.addWidget(self.master_input)
        layout.addWidget(self.totp_label)
        layout.addWidget(self.totp_input)
        layout.addWidget(self.login_btn)

        self.setLayout(layout)

    def handle_login(self):
        password = self.master_input.text()
        token = self.totp_input.text()

        if password != MASTER_PASSWORD:
            QMessageBox.critical(self, "Error", "Clave maestra incorrecta")
            return

        if not verify_totp(TOTP_SECRET, token):
            QMessageBox.critical(self, "Error", "Token 2FA incorrecto")
            return

        # Login exitoso → abrir Dashboard
        self.dashboard = DashboardWindow(password)
        self.dashboard.show()
        self.close()


# ===============================
# DASHBOARD WINDOW
# ===============================
class DashboardWindow(QWidget):
    def __init__(self, master_password):
        super().__init__()
        self.setWindowTitle("PassGuardian Dashboard")
        self.setMinimumSize(800, 600)

        # Instancias de seguridad y sincronización
        self.manager = SecretsManager(master_password)
        self.sync = SupabaseSync(self.manager)

        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()

        # Tabla de secretos
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Servicio", "Usuario"])
        self.table.horizontalHeader().setStretchLastSection(True)

        # Botones de acciones
        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Actualizar lista")
        self.refresh_btn.clicked.connect(self.load_data)

        self.sync_btn = QPushButton("Sincronizar con Supabase")
        self.sync_btn.clicked.connect(self.sync_all)

        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.sync_btn)

        layout.addLayout(btn_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def load_data(self):
        secrets = self.manager.list_secrets()
        self.table.setRowCount(len(secrets))
        for row_idx, secret in enumerate(secrets):
            self.table.setItem(row_idx, 0, QTableWidgetItem(secret["id"]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(secret["service"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(secret["user"]))

    def sync_all(self):
        try:
            self.sync.sync_all()
            QMessageBox.information(self, "Sincronización", "Sincronización completada")
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


# ===============================
# MAIN
# ===============================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = LoginWindow()
    login.show()
    sys.exit(app.exec())

