from PyQt5.QtWidgets import (
    QMainWindow, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QWidget, QMessageBox
)
from PyQt5.QtGui import QPixmap
import pyotp
import qrcode
from PIL.ImageQt import ImageQt
import time

from pathlib import Path

from src.infrastructure.user_manager import UserManager
from src.infrastructure.secrets_manager import SecretsManager


class LoginView(QMainWindow):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.user_manager = UserManager()
        self.current_secret = None

        self.failed_attempts = 0
        self.locked_until = None

        self.setWindowTitle("PassGuardian - Login")
        self.setGeometry(600, 300, 400, 350)

        try:
            layout = QVBoxLayout()

            self.username_label = QLabel("Username:")
            self.username_input = QLineEdit()
            layout.addWidget(self.username_label)
            layout.addWidget(self.username_input)

            self.password_label = QLabel("Master Password:")
            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.Password)
            layout.addWidget(self.password_label)
            layout.addWidget(self.password_input)

            self.totp_label = QLabel("TOTP Token:")
            self.totp_input = QLineEdit()
            layout.addWidget(self.totp_label)
            layout.addWidget(self.totp_input)

            self.qr_label = QLabel()
            layout.addWidget(self.qr_label)

            self.login_button = QPushButton("Login")
            self.login_button.clicked.connect(self.try_login)
            layout.addWidget(self.login_button)

            container = QWidget()
            container.setLayout(layout)
            self.setCentralWidget(container)

        except Exception as e:
            print("ERROR al construir LoginView:", repr(e))
            QMessageBox.critical(
                self,
                "Error crítico",
                f"Ocurrió un error al iniciar la pantalla de login:\n{e}"
            )

        # ----------------------------------------------------
        # CARGAR ESTILO QSS (MODERNO MINIMALISTA)
        # ----------------------------------------------------
        try:
            qss_path = Path(__file__).resolve().parent / "style.qss"
            if qss_path.exists():
                with open(qss_path, "r") as f:
                    self.setStyleSheet(f.read())
        except Exception as e:
            print("Error cargando estilo en LoginView:", repr(e))

    def try_login(self):
        try:
            if self.locked_until and time.time() < self.locked_until:
                remaining = int(self.locked_until - time.time())
                QMessageBox.warning(self, "Bloqueado", f"Espere {remaining} segundos.")
                return

            username = self.username_input.text().strip()
            master_password = self.password_input.text().strip()
            token = self.totp_input.text().strip()

            if not username:
                QMessageBox.warning(self, "Error", "Username requerido.")
                return

            if not master_password:
                QMessageBox.warning(self, "Error", "Debe ingresar la contraseña maestra.")
                return

            # Obtener o crear secret TOTP
            secret = self.user_manager.get_or_create_totp_secret()
            self.current_secret = secret

            # Verificar TOTP
            if not self.user_manager.verify_totp(secret, token):
                self.failed_attempts += 1
                self._check_lockout()
                QMessageBox.critical(self, "Error", "Código TOTP incorrecto.")
                return

            # Verificar contraseña maestra
            sm = SecretsManager(master_password)
            sm.get_all()
            sm.close()

            # Login exitoso
            self.failed_attempts = 0
            self.locked_until = None

            print(">>> LOGIN OK, LLAMANDO on_login_success")
            self.on_login_success(master_password, self.current_secret)
            print(">>> on_login_success TERMINÓ")

            # LIMPIEZA DE MEMORIA SENSIBLE
            master_password = None
            token = None
            username = None
            secret = None

            self.username_input.clear()
            self.password_input.clear()
            self.totp_input.clear()

            # NO CERRAMOS LA VENTANA TODAVÍA
            # self.close()


        except Exception as e:
            print("ERROR inesperado en try_login:", repr(e))
            QMessageBox.critical(
                self,
                "Error inesperado",
                f"Ocurrió un error inesperado durante el login:\n{e}"
            )

    def _check_lockout(self):
        try:
            if self.failed_attempts >= 5:
                self.locked_until = time.time() + 30
                QMessageBox.warning(self, "Bloqueado", "Espere 30 segundos.")
        except Exception as e:
            print("ERROR en _check_lockout:", repr(e))

    def show_qr(self, secret):
        try:
            qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q)
            uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=self.username_input.text(),
                issuer_name="PassGuardian"
            )
            qr.add_data(uri)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qt_img = ImageQt(qr_img)
            pixmap = QPixmap.fromImage(qt_img)
            self.qr_label.setPixmap(pixmap)
        except Exception as e:
            print("ERROR al generar QR:", repr(e))
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo generar el código QR:\n{e}"
            )

