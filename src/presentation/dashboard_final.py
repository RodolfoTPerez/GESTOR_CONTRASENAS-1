import sys
import base64
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QInputDialog
)
from PySide6.QtCore import Qt, QTimer
from datetime import datetime
from infrastructure.secrets_manager import SecretsManager
from infrastructure.supabase_sync import SupabaseSync
from infrastructure.security import (
    password_strength, generate_strong_password, verify_totp, encrypt_export, decrypt_import
)

# ===============================
# CONFIG
# ===============================
MASTER_PASSWORD = "MiClaveMaestra123!"  # Reemplazar con input seguro
TOTP_SECRET = "JBSWY3DPEHPK3PXP"

# ===============================
# LOGIN WINDOW
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

        self.dashboard = DashboardFinal(password)
        self.dashboard.show()
        self.close()

# ===============================
# DASHBOARD FINAL
# ===============================
class DashboardFinal(QWidget):
    def __init__(self, master_password):
        super().__init__()
        self.setWindowTitle("PassGuardian - Enterprise Dashboard")
        self.setMinimumSize(1000, 600)

        self.manager = SecretsManager(master_password)
        self.sync = SupabaseSync(self.manager)
        self.trash = []  # Papelera local

        self.dark_mode = False
        self.init_ui()
        self.load_data()
        self.start_clock()

    # -------------------------------
    # UI
    # -------------------------------
    def init_ui(self):
        layout = QVBoxLayout()

        # Botones principales
        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Actualizar lista")
        self.refresh_btn.clicked.connect(self.load_data)
        self.sync_btn = QPushButton("Sincronizar 🔄")
        self.sync_btn.clicked.connect(self.sync_all)
        self.add_btn = QPushButton("Agregar +")
        self.add_btn.clicked.connect(self.add_secret)
        self.export_btn = QPushButton("Exportar 🔐")
        self.export_btn.clicked.connect(self.export_secrets)
        self.import_btn = QPushButton("Importar 🔐")
        self.import_btn.clicked.connect(self.import_secrets)
        self.trash_btn = QPushButton("Papelera 🗑️")
        self.trash_btn.clicked.connect(self.show_trash)
        self.theme_btn = QPushButton("Modo Dark/Light 🌓")
        self.theme_btn.clicked.connect(self.toggle_theme)

        for b in [self.refresh_btn, self.sync_btn, self.add_btn,
                  self.export_btn, self.import_btn, self.trash_btn, self.theme_btn]:
            btn_layout.addWidget(b)

        # Tabla de secretos
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Servicio", "Usuario", "Fuerza", "Contraseña", "Acciones"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Reloj
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
            self.table.setItem(row_idx, 4, QTableWidgetItem("••••••••"))

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
            self.table.setCellWidget(row_idx, 5, action_widget)

    # -------------------------------
    # ACCIONES DE SECRETOS
    # -------------------------------
    def add_secret(self):
        service, ok1 = QInputDialog.getText(self, "Nuevo Servicio", "Nombre del servicio:")
        if not ok1 or not service:
            return

        # Validación duplicados
        existing = [s["service"] for s in self.manager.list_secrets()]
        if service in existing:
            QMessageBox.warning(self, "Duplicado", "El servicio ya existe")
            return

        user, ok2 = QInputDialog.getText(self, "Usuario", "Nombre de usuario:")
        if not ok2 or not user:
            return

        # Generar contraseña fuerte y mostrar barra de complejidad
        password = generate_strong_password()
        strength = password_strength(password)

        self.manager.create_secret(service, user, password)
        QMessageBox.information(self, "Contraseña generada",
                                f"Contraseña generada ({strength}%) para {service}")
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
            # Mover a papelera
            self.trash.append(self.manager.get_secret(secret_id))
            self.manager.delete_secret(secret_id)
            self.load_data()

    def show_trash(self):
        if not self.trash:
            QMessageBox.information(self, "Papelera", "Papelera vacía")
            return
        trash_text = "\n".join(self.trash)
        QMessageBox.information(self, "Papelera", trash_text)

    def copy_secret(self, secret_id):
        plaintext = self.manager.get_secret(secret_id)
        QApplication.clipboard().setText(plaintext)
        QMessageBox.information(self, "Copiar", "Contraseña copiada al portapapeles")

    def show_secret(self, secret_id):
        plaintext = self.manager.get_secret(secret_id)
        QMessageBox.information(self, "Contraseña", f"{plaintext}")

    # -------------------------------
    # DARK / LIGHT MODE
    # -------------------------------
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.setStyleSheet("background-color: #2b2b2b; color: #f0f0f0;")
        else:
            self.setStyleSheet("")

    # -------------------------------
    # EXPORT / IMPORT CIFRADO
    # -------------------------------
    def export_secrets(self):
        token, ok = QInputDialog.getText(self, "2FA requerido", "Ingrese token 2FA:")
        if not ok or not verify_totp(TOTP_SECRET, token):
            QMessageBox.warning(self, "Error", "Token 2FA inválido")
            return

        all_secrets = self.manager.list_secrets()
        encrypted_data = encrypt_export(all_secrets, MASTER_PASSWORD)
        with open("passguardian_export.enc", "wb") as f:
            f.write(encrypted_data)
        QMessageBox.information(self, "Exportación", "Datos exportados correctamente")

    def import_secrets(self):
        token, ok = QInputDialog.getText(self, "2FA requerido", "Ingrese token 2FA:")
        if not ok or not verify_totp(TOTP_SECRET, token):
            QMessageBox.warning(self, "Error", "Token 2FA inválido")
            return

        try:
            with open("passguardian_export.enc", "rb") as f:
                encrypted_data = f.read()
            secrets_list = decrypt_import(encrypted_data, MASTER_PASSWORD)
            for s in secrets_list:
                self.manager.create_secret(s["service"], s["user"], s["secret"])
            self.load_data()
            QMessageBox.information(self, "Importación", "Datos importados correctamente")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Falló importación: {str(e)}")

    # -------------------------------
    # SINCRONIZACIÓN
    # -------------------------------
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


