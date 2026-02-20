from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QFrame
)
from io import BytesIO
from PyQt5.QtCore import Qt
from src.domain.messages import MESSAGES
from src.presentation.ui_utils import PremiumMessage
from PyQt5.QtGui import QPixmap, QImage
import qrcode
import pyotp
import logging

from src.presentation.theme_manager import ThemeManager

class TwoFactorSetupDialog(QDialog):
    def __init__(self, user_manager, secrets_manager, username, parent=None):
        super().__init__(parent)
        self.username = username
        self.logger = logging.getLogger(__name__)
        self.setWindowTitle(MESSAGES.TWOFACTOR.SETUP_TITLE)
        self.setFixedSize(450, 700)
        from PyQt5.QtCore import QSettings
        self.settings = QSettings(ThemeManager.APP_ID, "VultraxCore_Global")
        self.theme = ThemeManager()
        active_theme = self.settings.value("theme_active", "tactical_dark")
        self.theme.set_theme(active_theme)
        
        # Fondo base instantáneo para evitar flasheo blanco
        colors = self.theme.get_theme_colors()
        self.setStyleSheet(f"QDialog {{ background-color: {colors['bg']}; }}")
        self.setStyleSheet(self.theme.load_stylesheet("dialogs"))

        self.user_manager = user_manager
        self.secrets_manager = secrets_manager
        
        # 1. Generar nuevo secreto temporal
        self.temp_secret = self.user_manager.generate_totp_secret()
        
        # 2. UI Layout
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Header
        title = QLabel(MESSAGES.TWOFACTOR.SETUP_HEADER)
        title.setObjectName("dialog_title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        lbl_info = QLabel(MESSAGES.TWOFACTOR.SETUP_DESC)
        lbl_info.setObjectName("dialog_subtitle")
        lbl_info.setWordWrap(True)
        lbl_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_info)

        # QR Code Container
        self.qr_container = QFrame()
        self.qr_container.setObjectName("QRContainer")
        self.qr_container.setFixedSize(340, 340)
        # El QRContainer debe ser blanco para que el QR sea escaneable
        # El QRContainer debe ser blanco para que el QR sea escaneable
        self.qr_container.setStyleSheet(self.theme.apply_tokens("background-color: white; border-radius: 20px; border: 4px solid @primary;"))
        qr_cont_layout = QVBoxLayout(self.qr_container)
        qr_cont_layout.setAlignment(Qt.AlignCenter)
        qr_cont_layout.setContentsMargins(0, 0, 0, 0)
        
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        qr_cont_layout.addWidget(self.qr_label)
        
        layout.addWidget(self.qr_container, 0, Qt.AlignCenter)
        self._generate_qr()

        # Secret Text (Manual Entry)
        lbl_manual = QLabel(f"{MESSAGES.TWOFACTOR.SETUP_MANUAL}\n{self.temp_secret}")
        lbl_manual.setStyleSheet(self.theme.apply_tokens("color: @text_dim; font-family: monospace; font-size: 12px;"))
        lbl_manual.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_manual)
        
        # Verify Input
        layout.addWidget(QLabel(MESSAGES.TWOFACTOR.SETUP_INPUT_LBL))
        self.input_code = QLineEdit()
        self.input_code.setPlaceholderText("000000")
        self.input_code.setMaxLength(6)
        self.input_code.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.input_code)
        
        # Actions
        btn_verify = QPushButton(MESSAGES.TWOFACTOR.SETUP_BTN_VERIFY)
        btn_verify.setObjectName("btn_primary")
        btn_verify.clicked.connect(self._verify_and_save)
        layout.addWidget(btn_verify)

    def _generate_qr(self):
        # Generar URI estándar para OTP
        uri = pyotp.totp.TOTP(self.temp_secret).provisioning_uri(
            name=self.username,
            issuer_name="Vultrax Core"
        )
        
        # QR con Máxima Corrección de errores y tamaño reducido para fácil enfoque
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=6,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir a QPixmap usando un Buffer persistente (FIX SENIOR para evitar cuadro blanco)
        buf = BytesIO()
        img.save(buf, format="PNG")
        
        qim = QImage()
        qim.loadFromData(buf.getvalue())
        
        # --- FIX SENIOR: Usamos el tamaño nativo 1:1 para evitar distorsión ---
        pix = QPixmap.fromImage(qim)
        self.qr_label.setPixmap(pix)
        self.qr_label.setFixedSize(pix.size())
        self.qr_label.setStyleSheet("border: none; background: transparent;")

    def _verify_and_save(self):
        code = self.input_code.text().strip()
        if not code.isdigit() or len(code) != 6:
            PremiumMessage.info(self, MESSAGES.TWOFACTOR.TITLE_INVALID, MESSAGES.TWOFACTOR.TEXT_NOT_6_DIGITS)
            return

        if self.user_manager.verify_totp(self.temp_secret, code):
            # 1. Guardar localmente en Meta y Perfil
            self.secrets_manager.set_meta("totp_secret", self.temp_secret)
            
            username = self.username
            profile = self.secrets_manager.get_local_user_profile(username)
            if profile:
                self.secrets_manager.save_local_user_profile(
                    username, profile["password_hash"], profile["salt"], 
                    profile["vault_salt"], profile["role"], 
                    profile.get("protected_key"), self.temp_secret
                )
            
            # 2. Sincronizar con la Nube (CIFRADO)
            master_pwd = getattr(self.secrets_manager, 'last_password', None)
            
            # FIX: El salt ya viene como bytes desde la DB local, no hay que decodificarlo de nuevo
            vault_salt = profile.get("vault_salt") if profile else None
            if isinstance(vault_salt, str): # Por si acaso viniera como string b64
                import base64
                try: vault_salt = base64.b64decode(vault_salt)
                except Exception as e:
                    self.logger.debug(f"Vault salt base64 decoding failed during 2FA setup: {e}")
            
            self.logger.info(f"Syncing 2FA for {username} with cloud...")
            cloud_success = self.user_manager.save_totp_secret(username, self.temp_secret, master_pwd, vault_salt)
            
            if cloud_success:
                PremiumMessage.success(self, MESSAGES.TWOFACTOR.SETUP_SUCCESS_TITLE, MESSAGES.TWOFACTOR.SETUP_SUCCESS_TEXT)
                self.accept()
            else:
                PremiumMessage.warning(self, MESSAGES.TWOFACTOR.SETUP_WARN_TITLE, MESSAGES.TWOFACTOR.SETUP_WARN_TEXT)
                self.accept()
        else:
            PremiumMessage.error(self, MESSAGES.TWOFACTOR.TITLE_FAIL, MESSAGES.TWOFACTOR.TEXT_FAIL)
