from PyQt5.QtWidgets import (
    QMainWindow, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QFrame,
    QGraphicsDropShadowEffect, QApplication
)
from PyQt5.QtGui import QPixmap, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPropertyAnimation, QPoint, QSettings, QTimer
import pyotp
import qrcode
from PIL.ImageQt import ImageQt
import time
import base64
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

from src.infrastructure.user_manager import UserManager
from src.infrastructure.secrets_manager import SecretsManager
from src.presentation.ui_utils import PremiumMessage
from src.domain.messages import MESSAGES


class LoginView(QMainWindow):
    def __init__(self, user_manager=None):
        super().__init__()
        self.user_manager = user_manager or UserManager()
        self.on_login_success = None
        self.current_secret = None

        self.failed_attempts = 0
        self.locked_until = None
        self._drag_pos = None

        # --- WINDOW CONFIGURATION ---
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(900, 550)
        self.center_on_screen()

        # --- MAIN CONTAINER (Rounded & Shadow) ---
        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(self.central_widget)

        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- SHADOW EFFECT ---
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.central_widget.setGraphicsEffect(shadow)

        # ============================================================
        #   LEFT PANEL: HERO SECTION
        # ============================================================
        self.left_frame = QFrame()
        self.left_frame.setObjectName("LeftFrame")
        self.left_layout = QVBoxLayout(self.left_frame)
        self.left_layout.setContentsMargins(40, 60, 40, 60)
        self.left_layout.setAlignment(Qt.AlignCenter)

        # Logo / Icon
        self.logo_label = QLabel()
        # Cargar logo anterior
        logo_path = str(Path(__file__).parent.parent.parent / "logo_v2.png")
        
        if Path(logo_path).exists():
            pixmap = QPixmap(logo_path)
            # Escalar manteniendo aspecto
            scaled_pixmap = pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled_pixmap)
        else:
            # Fallback a emoji si no existe
            self.logo_label.setText("🛡️")
            self.logo_label.setStyleSheet("font-size: 80px; background: transparent; color: white;")
        
        # App Name
        self.app_title = QLabel("PassGuardian")
        self.app_title.setAlignment(Qt.AlignCenter)
        self.app_title.setStyleSheet("font-size: 32px; font-weight: bold; color: white;")

        # Tagline
        self.tagline = QLabel("Seguridad profesional\npara tus credenciales.")
        self.tagline.setAlignment(Qt.AlignCenter)
        self.tagline.setStyleSheet("font-size: 16px; color: rgba(255,255,255,0.8); margin-top: 10px;")

        self.left_layout.addWidget(self.logo_label)
        self.left_layout.addWidget(self.app_title)
        self.left_layout.addWidget(self.tagline)
        self.left_layout.addStretch()

        self.copyright_label = QLabel("© 2026 PassGuardian Secure")
        self.copyright_label.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 10px;")
        self.copyright_label.setAlignment(Qt.AlignCenter)
        self.left_layout.addWidget(self.copyright_label)


        # ============================================================
        #   RIGHT PANEL: LOGIN FORM
        # ============================================================
        self.right_frame = QFrame()
        self.right_frame.setObjectName("RightFrame")
        self.right_frame.setStyleSheet("background-color: #ffffff; border-top-right-radius: 15px; border-bottom-right-radius: 15px;")
        
        # Sub-layout for right frame
        self.right_layout = QVBoxLayout(self.right_frame)
        self.right_layout.setContentsMargins(40, 30, 40, 40)
        self.right_layout.setSpacing(15)

        # --- WINDOW CONTROLS (Top Right) ---
        self.controls_layout = QHBoxLayout()
        self.controls_layout.setAlignment(Qt.AlignRight | Qt.AlignTop)
        
        self.btn_min = QPushButton("─")
        self.btn_min.setFixedSize(30, 30)
        self.btn_min.setCursor(Qt.PointingHandCursor)
        self.btn_min.clicked.connect(self.showMinimized)
        self.btn_min.setStyleSheet("border:none; font-weight:bold; color: #555;")

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(30, 30)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.clicked.connect(self.close)
        self.btn_close.setStyleSheet("QPushButton { border:none; font-weight:bold; color: #555; } QPushButton:hover { color: red; }")

        self.controls_layout.addWidget(self.btn_min)
        self.controls_layout.addWidget(self.btn_close)
        
        self.right_layout.addLayout(self.controls_layout)

        # Greeting
        self.welcome_label = QLabel(MESSAGES.LOGIN.WELCOME)
        self.welcome_label.setObjectName("welcome_label")
        self.welcome_label.setStyleSheet("font-size: 32px; font-weight: 900; color: #334155; letter-spacing: 2px;")
        self.welcome_label.setAlignment(Qt.AlignLeft)
        self.right_layout.addWidget(self.welcome_label)
        
        self.subtitle_label = QLabel(MESSAGES.LOGIN.SUBTITLE)
        self.subtitle_label.setObjectName("subtitle_label")
        self.subtitle_label.setStyleSheet("font-size: 13px; color: #64748b; font-weight: 700; font-family: 'Consolas'; margin-bottom: 20px;")
        self.subtitle_label.setAlignment(Qt.AlignLeft)
        self.right_layout.addWidget(self.subtitle_label)

        # Inputs
        self.username_input = self._create_input("OPERATOR_ID")
        self.right_layout.addWidget(self.username_input)

        self.password_input = self._create_input("MASTER_SIGNATURE", password=True)
        self.right_layout.addWidget(self.password_input)

        self.totp_input = self._create_input("2FA_TOKEN")
        self.totp_input.hide() # OCULTO POR DEFECTO PARA CLEAN UI
        self.right_layout.addWidget(self.totp_input)

        # QR Label (Hidden by default, used if needed)
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.right_layout.addWidget(self.qr_label)

        self.right_layout.addStretch()

        # Login BUTTON
        self.login_button = QPushButton(MESSAGES.LOGIN.BTN_LOGIN)
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.setFixedHeight(45)
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #2d7dca;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #3ea1ff;
            }
            QPushButton:pressed {
                background-color: #1e5a92;
            }
        """)
        self.login_button.clicked.connect(self.try_login)
        self.right_layout.addWidget(self.login_button)

        # --- ADD FRAMES TO MAIN LAYOUT ---
        self.main_layout.addWidget(self.left_frame, 40) # 40% width
        self.main_layout.addWidget(self.right_frame, 60) # 60% width

        # --- APPLY THEME ---
        self._apply_branding()


    def _create_input(self, placeholder, password=False):
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        if password:
            inp.setEchoMode(QLineEdit.Password)
        inp.setFixedHeight(40)
        inp.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 0 10px;
                font-size: 14px;
                background-color: #f9f9f9;
                color: #333;
            }
            QLineEdit:focus {
                border: 2px solid #2d7dca;
                background-color: #fff;
            }
        """)
        return inp

    def _apply_branding(self):
        # Load theme setting
        settings = QSettings("PassGuardian", "MiDashboard")
        tema_actual = settings.value("tema_actual", "Claro")

        # Define styles based on theme
        # We'll use gradients for the Left Frame to make it "Spectacular"
        gradients = {
            "Claro": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #4facfe, stop:1 #00f2fe)",
            "Oscuro": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #434343, stop:1 #000000)",
            "Graphite Pro": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #232526, stop:1 #414345)",
            "Emerald Pro": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #11998e, stop:1 #38ef7d)",
            "Ruby Pro": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #cb2d3e, stop:1 #ef473a)",
            "Purple VS Pro": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #8E2DE2, stop:1 #4A00E0)",
            "Carbon Steel Pro": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #616161, stop:1 #9bc5c3)",
            "Sandstone Executive": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #DECBA4, stop:1 #3E5151)",
            "CyberBlue Quantum": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #00c6ff, stop:1 #0072ff)",
            "Inferno Neon Pro": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #f12711, stop:1 #f5af19)",
            "Ultraviolet Pulse": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #654ea3, stop:1 #eaafc8)"
        }

        bg_gradient = gradients.get(tema_actual, gradients["Claro"])

        # Update Left Frame Style
        self.left_frame.setStyleSheet(f"""
            QFrame#LeftFrame {{
                background: {bg_gradient};
                border-top-left-radius: 15px;
                border-bottom-left-radius: 15px;
            }}
        """)
        
        # --- BUTTON COLOR LOGIC ---
        # Extract a solid color from the gradient map for the button
        # We define a map of primary solid colors corresponding to the themes
        button_colors = {
            "Claro": "#4facfe", # Blue from gradient
            "Oscuro": "#434343", # Dark Grey
            "Graphite Pro": "#414345", 
            "Emerald Pro": "#11998e", # Green
            "Ruby Pro": "#cb2d3e", # Red
            "Purple VS Pro": "#8E2DE2", # Purple
            "Carbon Steel Pro": "#616161",
            "Sandstone Executive": "#BFA57D", # Gold/Sandstone approximate
            "CyberBlue Quantum": "#0072ff", # Blue
            "Inferno Neon Pro": "#ff0000", # Pure Red for maximum impact
            "Ultraviolet Pulse": "#654ea3" # Violet
        }
        
        # Si el usuario quiere ver ROJO y no lo ve, tal vez su tema guardado es "Claro" (default).
        # Vamos a asegurar que si el tema es "Inferno Neon Pro", el botón sea ROJO INTENSO.
        
        btn_color = button_colors.get(tema_actual, "#2d7dca")

        # FIX: Si el tema es Inferno, asegurar gradiente ROJO
        if tema_actual == "Inferno Neon Pro":
             pass # Ya está en el mapa
        
        self.login_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_color};
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {btn_color}AA; /* Add transparency for hover or similar */
                border: 1px solid #fff;
            }}
            QPushButton:pressed {{
                background-color: #333;
            }}
        """)

        # If theme is 'Oscuro' or dark variants, right frame should probably be dark too?
        # User asked for "Professional". Dark login forms are cool.
        is_dark = tema_actual in ["Oscuro", "Graphite Pro", "Carbon Steel Pro"]
        
        if is_dark:
            self.right_frame.setStyleSheet("""
                QFrame#RightFrame {
                    background-color: #1e1e1e;
                    border-top-right-radius: 15px;
                    border-bottom-right-radius: 15px;
                }
            """)
            self.welcome_label.setStyleSheet("font-size: 26px; font-weight: bold; color: #fff;")
            self.subtitle_label.setStyleSheet("font-size: 14px; color: #aaa; margin-bottom: 20px;")
            input_style = """
                QLineEdit {
                    border: 2px solid #444;
                    border-radius: 8px;
                    padding: 0 10px;
                    font-size: 14px;
                    background-color: #2d2d2d;
                    color: #fff;
                }
                QLineEdit:focus {
                    border: 2px solid #00c6ff;
                    background-color: #333;
                }
            """
            self.username_input.setStyleSheet(input_style)
            self.password_input.setStyleSheet(input_style)
            self.totp_input.setStyleSheet(input_style)
            
            self.btn_min.setStyleSheet("border:none; font-weight:bold; color: #bbb;")
            self.btn_close.setStyleSheet("QPushButton { border:none; font-weight:bold; color: #bbb; } QPushButton:hover { color: red; }")


    # --- DRAG LOGIC ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry().center()
        self.move(screen.x() - self.width() // 2, screen.y() - self.height() // 2)

    def fade_and_close(self):
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(300)
        self.anim.setStartValue(1)
        self.anim.setEndValue(0)
        self.anim.finished.connect(self.close)
        self.anim.start()

    def try_login(self):
        try:
            if self.locked_until and time.time() < self.locked_until:
                remaining = int(self.locked_until - time.time())
                PremiumMessage.error(self, MESSAGES.LOGIN.TITLE_BLOCKED, MESSAGES.LOGIN.TEXT_BLOCKED.format(remaining=remaining))
                return

            username = self.username_input.text().strip()
            master_password = self.password_input.text().strip()
            token = self.totp_input.text().strip()

            if not username or not master_password:
                PremiumMessage.info(self, MESSAGES.LOGIN.TITLE_FIELDS_REQ, MESSAGES.LOGIN.TEXT_FIELDS_REQ)
                return

            # 0. PREPARAR BASE DE DATOS ESPECIFÍCA DEL USUARIO
            self.user_manager.prepare_for_user(username)

            # 1. VALIDACIÓN DE USUARIO (Online → Offline Fallback)
            user_profile = self.user_manager.validate_user_access(username)
            is_offline = (user_profile is None)
            
            if is_offline:
                # MODO OFFLINE: Validar contra DB local
                local_res = self.user_manager.check_local_login(username, master_password)
                if not local_res:
                    PremiumMessage.error(self, MESSAGES.LOGIN.TITLE_OFFLINE_ERROR, MESSAGES.LOGIN.TEXT_OFFLINE_NO_PROFILE)
                    return
                if local_res["status"] == "error":
                    PremiumMessage.error(self, MESSAGES.LOGIN.TITLE_AUTH_ERROR, MESSAGES.LOGIN.TEXT_WRONG_PWD)
                    return
                if local_res["status"] == "needs_setup":
                    PremiumMessage.error(self, MESSAGES.LOGIN.TITLE_SETUP_REQ, MESSAGES.LOGIN.TEXT_SETUP_REQ)
                    return
                
                final_profile = local_res["profile"]
            else:
                # MODO ONLINE: Validar contra Supabase
                if not user_profile["exists"]:
                    PremiumMessage.error(self, MESSAGES.LOGIN.TITLE_AUTH_ERROR, MESSAGES.LOGIN.TEXT_USER_NOT_EXISTS.format(username=username))
                    return
                if not user_profile["active"]:
                    PremiumMessage.error(self, MESSAGES.LOGIN.TITLE_AUTH_ERROR, MESSAGES.LOGIN.TEXT_INACTIVE)
                    return
                
                # CASO A: Usuario nuevo (Sin contraseña configurada aún)
                if not user_profile["password_hash"]:
                    confirm = PremiumMessage.question(self, MESSAGES.LOGIN.TITLE_NEW_ACCOUNT, MESSAGES.LOGIN.TEXT_CONFIRM_PWD.format(username=username))
                    if not confirm: return
                    
                    success, vault_salt = self.user_manager.update_user_password(username, master_password)
                    if not success:
                        PremiumMessage.error(self, "Error", "No se pudo establecer la contraseña en la nube.")
                        return
                    # Actualizar perfil local tras configurar
                    user_profile["vault_salt"] = base64.b64encode(vault_salt).decode('ascii')
                
                # CASO B: Verificar contra el hash de la nube
                else:
                    is_valid = self.user_manager.verify_password(master_password, user_profile["salt"], user_profile["password_hash"])
                    if not is_valid:
                        self.failed_attempts += 1
                        self._check_lockout()
                        PremiumMessage.error(self, MESSAGES.LOGIN.TITLE_AUTH_ERROR, MESSAGES.LOGIN.TEXT_WRONG_PWD_CLOUD)
                        return
                    
                    # Sincronizamos a local inmediatamente tras validar Online
                    self.user_manager.sync_user_to_local(username, user_profile)
                    final_profile = user_profile

            # --- VERIFICACIÓN DE SEGURIDAD POST-AUTH (SENIOR SHIELD) ---
            # Este bloque se ejecuta SIEMPRE, tanto Online como Offline
            # --- VERIFICACIÓN DE SEGURIDAD REDUNDANTE (TRIPLE CHECK) ---
            # 1. Probar perfil actual (Sync)
            totp_secret = final_profile.get("totp_secret")
            
            logger.debug(f"DEBUG LOGIN - User: {username}")
            logger.debug(f"DEBUG LOGIN - Token entered: '{token}'")
            logger.debug(f"DEBUG LOGIN - Secret retrieved: '{totp_secret}'")
            
            # 2. Probar meta local (Legacy/Backup)
            if not totp_secret:
                totp_secret = self.user_manager.sm.get_meta("totp_secret")
                
            # 3. Probar nube directamente (Si hay internet)
            if not totp_secret:
                totp_secret = self.user_manager.get_user_totp_secret(username)

            if totp_secret and len(str(totp_secret).strip()) > 5:
                logger.info(f"Security: 2FA ENABLED for {username}.")
                if not token:
                    self.totp_input.show() # MOSTRAR DINÁMICAMENTE
                    self.totp_input.setFocus()
                    PremiumMessage.info(self, "2FA REQUERIDO", "Inyecte su Token de Seguridad para validar la firma.")
                    return
                
                if not self.user_manager.verify_totp(totp_secret, token):
                    logger.warning(f"Lockout: Incorrect 2FA code for {username}")
                    PremiumMessage.error(self, "2FA Inválido", "El código 2FA es incorrecto o ha expirado.")
                    return
                logger.info("2FA OK.")
            else:
                # REGLA DE ORO DE SEGURIDAD (ANTI-BYPASS):
                # Si el usuario ingresó algo en el campo de token pero NO encontramos el secreto,
                # bloqueamos por seguridad. Significa que hay un desajuste y no debemos arriesgar.
                if token and len(token) > 0:
                    logger.critical(f"Critical: Token entered for {username} but secret is inaccessible or non-existent.")
                    PremiumMessage.error(self, "Error de Seguridad", "No se pudo verificar tu 2FA porque el secreto no está configurado o es inaccesible. Si crees que esto es un error, contacta al administrador.")
                    return
                logger.info(f"Info: User {username} without active 2FA.")

            # 2. LOGIN EXITOSO
            self.current_user_profile = {
                "username": username.upper(),
                "role": final_profile["role"],
                "totp_secret": totp_secret
            }
            
            logger.info(f"LOGIN OK: {username} ({final_profile['role']})")
            self.failed_attempts = 0
            self.on_login_success(master_password, totp_secret, self.current_user_profile)

            self.username_input.clear()
            self.password_input.clear()
            self.fade_and_close()

        except Exception as e:
            logger.exception(f"Unexpected error in try_login: {repr(e)}")
            PremiumMessage.error(self, MESSAGES.LOGIN.TITLE_SYSTEM_ERROR, MESSAGES.LOGIN.TEXT_UNEXPECTED.format(error=str(e)))

    def _check_lockout(self):
        if self.failed_attempts >= 5:
            self.locked_until = time.time() + 30
            PremiumMessage.error(self, MESSAGES.LOGIN.TITLE_BLOCKED, MESSAGES.LOGIN.TEXT_BLOCKED.format(remaining=30))

    def show_qr(self, secret):
        # Implementation if needed for first time setup, 
        # can display in a modal or expand the window 
        # For now simple placeholder to match previous functionality
        pass
