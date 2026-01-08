import sys
import secrets as py_secrets
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt, QTimer
from infrastructure.secrets_manager import SecretsManager
from infrastructure.supabase_sync import SupabaseSync
from infrastructure.security import password_strength, generate_strong_password, verify_totp
from datetime import datetime

# ===============================
# CONFIG
# ===============================
MASTER_PASSWORD = "MiClaveMaestra123!"  # en práctica, pedir input
TOTP_SECRET = "JBSWY3DPEHPK3PXP"

# ===============================
# LOGIN (REUTILIZAMOS)
# ===============================
class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PassGuardian Login")
        self.setFixedSize(400, 220)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.master_label = QLabel("Clave Maestra:")
        self.master_input = QLineEdit()
        self.master_input.setEchoMode(QLineEdit.Password)

        self.totp_label = QLabel("Token 2FA:")
        self.totp_input = QLineEdit()

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

        # Abrir Dashboard completo
        self.dashboard = DashboardFull(password)
        self.dashboard.show()
        self.close()

# ===============================
# DASHBOARD COMPLETO
# ===============================
class DashboardFull(QWidget):
    def __init__(self, master_password):
        super().__init__()
        self.setWindowTitle("PassGuardian - Dashboard Enterprise")
        self.setMinimumSize(900, 600)

        # Instancias de seguridad y sincronización
        self.manager = SecretsManager(master_password)
        self.sync = SupabaseSync(self.manager)

        self.init_ui()
        self.load_data()
        self.start_clock()

    # -------------------------------
    # UI
    # -------------------------------
    def init_ui(self):
        layout = QVBoxLayout()

        # Tabla de secretos
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Servicio", "Usuario", "Fuerza", "Acciones"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Botones superiores
        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Actualizar lista")
        self.refresh_btn.clicked.connect(self.load_data)
        self.sync_btn = QPushButton("Sincronizar 🔄")
        self.sync_btn.clicked.connect(self.sync_all)
        self.add_btn = QPushButton("Agregar +")
        self.add_btn.clicked.connect(self.add_secret)

        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.sync_btn)
        btn_layout.addWidget(self.add_btn)

        # Label de reloj
        self.clock_label = QLabel("")
        self.clock_label.setAlignment(Qt.AlignRight)

        layout.addLayout(btn_layout)
        layout.addWidget(self.table)
        layout.addWidget(self.clock_label)
        self.setLayout(layout)

    # -------------------------------
    # RELOJ
    # -------------------------------
    def start_clock(self):
        timer = QTimer(self)
        timer.timeout.connect(self.update_clock)
        timer.start(1000)
        self.update_clock()

    def update_clock(self):
        self.clock_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # -------------------------------
    # CARGAR DATOS
    # -------------------------------
    def load_data(self):
        secrets = self.manager.list_secrets()
        self.table.setRowCount(len(secrets))
        for row_idx, secret in enumerate(secrets):
            self.table.setItem(row_idx, 0, QTableWidgetItem(secret["id"]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(secret["service"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(secret["user"]))

            # Fuerza de contraseña
            try:
                plaintext = self.manager.get_secret(secret["id"])
                score = password_strength(plaintext)
                if score < 40:
                    strength_text = "Débil 🔓"
                elif score < 70:
                    strength_text = "Media ⚠️"
                else:
                    strength_text = "Fuerte 🔒"
            except Exception:
                strength_text = "N/A"

            self.table.setItem(row_idx, 3, QTableWidgetItem(strength_text))

            # Acciones
            action_widget = QWidget()
            h_layout = QHBoxLayout()
            h_layout.setContentsMargins(0, 0, 0, 0)

            edit_btn = QPushButton("✏️")
            edit_btn.clicked.connect(lambda _, sid=secret["id"]: self.edit_secret(sid))
            delete_btn = QPushButton("🗑️")
            delete_btn.clicked.connect(lambda _, sid=secret["id"]: self.delete_secret(sid))
            copy_btn = QPushButton("📋")
            copy_btn.clicked.connect(lambda _, sid=secret["id"]: self.copy_secret(sid))
            show_btn = QPushButton("👁️")
            show_btn.clicked.connect(lambda _, sid=secret["id"]: self.show_secret(sid))

            for b in [edit_btn, delete_btn, copy_btn, show_btn]:
                h_layout.addWidget(b)
            action_widget.setLayout(h_layout)
            self.table.setCellWidget(row_idx, 4, action_widget)

    # -------------------------------
    # ACCIONES
    # -------------------------------
    def add_secret(self):
        service, ok1 = QInputDialog.getText(self, "Nuevo Servicio", "Nombre del servicio:")
        if not ok1 or not service:
            return
        user, ok2 = QInputDialog.getText(self, "Usuario", "Nombre de usuario:")
        if not ok2 or not user:
            return

        # Generar contraseña fuerte
        password = generate_strong_password()
        self.manager.create_secret(service, user, password)
        self.load_data()

    def edit_secret(self, secret_id):
        plaintext = self.manager.get_secret(secret_id)
        new_password, ok = QInputDialog.getText(self, "Editar Contraseña",
                                                f"Editar password para {secret_id}:",
                                                QLineEdit.Password,
                                                plaintext)
        if ok:
            self.manager.update_secret(secret_id, new_password)
            self.load_data()

    def delete_secret(self, secret_id):
        confirm = QMessageBox.question(self, "Eliminar", "¿Seguro desea eliminar?")
        if confirm == QMessageBox.Yes:
            self.manager.delete_secret(secret_id)
            self.load_data()

    def copy_secret(self, secret_id):
        plaintext = self.manager.get_secret(secret_id)
        QApplication.clipboard().setText(plaintext)
        QMessageBox.information(self, "Copiar", "Contraseña copiada al portapapeles")

    def show_secret(self, secret_id):
        plaintext = self.manager.get_secret(secret_id)
        QMessageBox.information(self, "Contraseña", f"{plaintext}")

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

