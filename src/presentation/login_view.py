from PySide6.QtWidgets import QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
from PySide6.QtGui import QPixmap
import pyotp
import qrcode
from PIL.ImageQt import ImageQt
from src.infrastructure.user_manager import UserManager

class LoginView(QMainWindow):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.user_manager = UserManager()
        self.current_secret = None

        self.setWindowTitle("PassGuardian - Login")
        self.setGeometry(600, 300, 400, 300)

        self.layout = QVBoxLayout()

        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        self.layout.addWidget(self.username_label)
        self.layout.addWidget(self.username_input)

        self.totp_label = QLabel("TOTP Token:")
        self.totp_input = QLineEdit()
        self.layout.addWidget(self.totp_label)
        self.layout.addWidget(self.totp_input)

        self.qr_label = QLabel()
        self.layout.addWidget(self.qr_label)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.try_login)
        self.layout.addWidget(self.login_button)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

    def try_login(self):
        username = self.username_input.text().strip()
        token = self.totp_input.text().strip()

        if not username:
            self.username_label.setText("Username: (required)")
            return

        # Obtiene o crea secret TOTP
        secret = self.user_manager.get_or_create_totp_secret()

        self.current_secret = secret

        # Verifica token
        if self.user_manager.verify_totp(secret, token):
            self.on_login_success(secret)
            self.close()
        else:
            self.totp_label.setText("TOTP Token: (invalid)")

    def show_qr(self, secret):
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=self.username_input.text(), issuer_name="PassGuardian")
        qr.add_data(uri)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qt_img = ImageQt(qr_img)
        pixmap = QPixmap.fromImage(qt_img)
        self.qr_label.setPixmap(pixmap)

