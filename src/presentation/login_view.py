from PyQt5.QtWidgets import (
    QMainWindow, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QFrame,
    QGraphicsDropShadowEffect, QApplication, QSpacerItem, QSizePolicy,
    QProgressBar
)
from PyQt5.QtGui import QPixmap, QColor, QFont, QIcon, QPainter, QLinearGradient, QRadialGradient, QConicalGradient
from PyQt5.QtCore import Qt, QPropertyAnimation, QPoint, QSettings, QTimer, QRect
import pyotp
import time
import base64
import logging
from pathlib import Path

from src.infrastructure.user_manager import UserManager
from src.infrastructure.secrets_manager import SecretsManager
from src.presentation.ui_utils import PremiumMessage
from src.presentation.theme_manager import ThemeManager
from src.domain.messages import MESSAGES

class PremiumLineEdit(QLineEdit):
    def __init__(self, placeholder, password=False):
        super().__init__()
        self.setPlaceholderText(placeholder)
        if password:
            self.setEchoMode(QLineEdit.Password)
        self.setFixedHeight(50)
        self._border_color = "#334155"
        self.setStyleSheet(self._style())
        
    def _style(self, active=False):
        theme = ThemeManager()
        colors = theme.get_theme_colors()
        
        border_color = "@primary" if active else "@ghost_primary_15"
        bg = "@bg" if active else "@bg_sec"
        text_color = "@accent"
        border_radius = "@border-radius-main"
        
        return theme.apply_tokens(f"""
            QLineEdit {{
                border: 2px solid {border_color};
                border-radius: {border_radius};
                padding: 0 15px;
                font-size: 14px;
                font-weight: 800;
                font-family: 'Consolas', monospace;
                background-color: {bg};
                color: {text_color};
            }}
        """)
        
    def focusInEvent(self, e):
        self.setStyleSheet(self._style(True))
        super().focusInEvent(e)
        
    def focusOutEvent(self, e):
        self.setStyleSheet(self._style(False))
        super().focusOutEvent(e)

class ConnectivityLED(QWidget):
    """Widget que simula un LED fluorescente giratorio para el estado de red."""
    def __init__(self):
        super().__init__()
        self.setFixedSize(24, 24)
        self._online = True
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._timer.start(30) # 33 FPS aprox

    def set_state(self, is_online):
        self._online = is_online
        self.update()

    def _rotate(self):
        self._angle = (self._angle + 10) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect().adjusted(2, 2, -2, -2)
        center = rect.center()
        radius = rect.width() / 2
        
        # Glow Fluorescente
        glow = QRadialGradient(center, radius + 4)
        if self._online:
            base_col = QColor(0, 255, 255) # Cian Neón
            glow.setColorAt(0, QColor(0, 255, 255, 200))
            glow.setColorAt(0.5, QColor(0, 150, 255, 100))
            glow.setColorAt(1, Qt.transparent)
        else:
            base_col = QColor(255, 50, 0) # Naranja/Rojo Neón
            glow.setColorAt(0, QColor(255, 80, 0, 200))
            glow.setColorAt(0.5, QColor(200, 0, 0, 100))
            glow.setColorAt(1, Qt.transparent)
            
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.rect())
        
        # Efecto Giratorio (Cónico)
        rot_grad = QConicalGradient(center, self._angle)
        rot_grad.setColorAt(0, base_col)
        rot_grad.setColorAt(0.2, Qt.transparent)
        rot_grad.setColorAt(1, Qt.transparent)
        
        painter.setBrush(rot_grad)
        painter.drawEllipse(rect)
        
        # Punto Central Intenso
        painter.setBrush(QColor(255, 255, 255, 200))
        painter.drawEllipse(center, 2, 2)

class LoginView(QMainWindow):
    def __init__(self, user_manager=None, prefill_user=None, on_success=None):
        super().__init__()
        from src.infrastructure.user_manager import UserManager
        self.user_manager = user_manager if isinstance(user_manager, UserManager) else UserManager()
        self.on_login_success = on_success if on_success else (user_manager if callable(user_manager) else None)
        
        self.prefill_user = prefill_user
        self.failed_attempts = 0
        self.locked_until = None
        self.reg_mode = False
        self._drag_pos = None  # Initialize drag position for window dragging

        self.logger = logging.getLogger(__name__)

        # --- WINDOW SETUP ---
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(1000, 650)
        self.center_on_screen()

        self._init_ui()
        self._apply_branding()
        self._init_inactivity_timer()

    def _init_inactivity_timer(self):
        """Inicia el protocolo de inactividad de forma segura (Watcher Externo)."""
        from src.presentation.inactivity_watcher import GlobalInactivityWatcher
        
        # [SENIOR FIX] El Login usa un timeout GLOBAL o el del último usuario conocido
        # para evitar que la pantalla de login se quede encendida para siempre.
        settings = QSettings(ThemeManager.APP_ID, "VultraxCore_Global")
        timeout_min = int(settings.value("auto_lock_time", 5)) # 5 min default para login
        timeout_ms = timeout_min * 60 * 1000
        
        # Delegamos en el Watcher Global (SINGLETON)
        self.watcher = GlobalInactivityWatcher.get_instance(timeout_ms, self._show_lock_screen_from_login)
        self.watcher.start()
        
        self.logger.info(f"Global Watcher active ({timeout_min} Min)")

    # [CLEANUP] Ya no necesitamos eventFilter ni installEventFilter aquí
    # El watcher se encarga de todo.

    def _show_lock_screen_from_login(self):
        """Despliega la esfera de neón tras inactividad en el Login."""
        if not self.isVisible(): return
        
        self.logger.info("Inactivity reached in Login. Deploying Vault Core.")
        if hasattr(self, "watcher"): self.watcher.stop()
        self.hide()
        
        try:
            from src.presentation.widgets.lock_sphere import HyperRealVaultCore
            v_name = self.user_manager.sm.get_meta("instance_name") or "PASSGUARDIAN"
            
            self.lock_screen = HyperRealVaultCore(vault_name=v_name)
            # Al volver (ENTER), simplemente mostramos el login de nuevo
            self.lock_screen.unlocked.connect(self._restore_from_lock)
            self.lock_screen.show()
        except Exception as e:
            self.logger.error(f"Failed to load lock screen sphere: {e}")
            self.show()

    def _restore_from_lock(self):
        """Regresa al Login tras la interacción con la esfera."""
        self.logger.info("Restoring access from lock sphere.")
        self.show()
        
        # Reactivar watcher
        if hasattr(self, "watcher"): self.watcher.start()
        self.logger.info("Watcher reactivated.")
            
        # Limpieza de referencia para evitar leaks
        if hasattr(self, "lock_screen"):
            self.lock_screen = None

    def _init_ui(self):
        # Iniciar gestor de temas
        self.theme_manager = ThemeManager()
        self.setStyleSheet(self.theme_manager.load_stylesheet("login"))
        
        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(self.central_widget)
        
        # Main Layout (Centered)
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignCenter)

        # 1. EL CONTENEDOR TIPO TARJETA (Glass Card)
        self.card = QFrame()
        self.card.setObjectName("MainCard")
        self.card.setFixedSize(460, 620)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)
        main_layout.addWidget(self.card)

        # --- HEADER AREA (Logo + Controls) ---
        header_area = QFrame()
        header_area.setObjectName("HeaderArea")
        header_area.setFixedHeight(220)
        header_vbox = QVBoxLayout(header_area)
        header_vbox.setContentsMargins(20, 15, 20, 0)
        
        # Windows Controls & Connectivity Row
        top_row = QHBoxLayout()
        
        # Connectivity Monitor (LED)
        self.conn_widget = QWidget()
        self.conn_widget.setFixedSize(120, 40)
        self.conn_widget.setObjectName("ConnMonitor")
        conn_layout = QHBoxLayout(self.conn_widget)
        conn_layout.setContentsMargins(10, 0, 10, 0)
        
        self.conn_led = ConnectivityLED()
        
        self.conn_label = QLabel("SYSTEM ONLINE")
        self.conn_label.setObjectName("ConnLabel")
        self.conn_label.setStyleSheet("color: #00ffff; font-family: 'Consolas'; font-size: 10px; font-weight: bold;")
        
        conn_layout.addWidget(self.conn_led)
        conn_layout.addWidget(self.conn_label)
        
        # Posicionamiento absoluto en la tarjeta (Superior Derecha)
        self.conn_widget.setParent(self.card)
        self.conn_widget.move(self.card.width() - 130, 15)
        
        top_row.addStretch()
        
        self.btn_min = QPushButton("－")
        self.btn_min.setObjectName("btn_min")
        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("btn_close")
        for b in [self.btn_min, self.btn_close]:
            b.setFixedSize(28, 28)
            b.setCursor(Qt.PointingHandCursor)
        self.btn_min.clicked.connect(self.showMinimized)
        self.btn_close.clicked.connect(self.close)
        top_row.addWidget(self.btn_min)
        top_row.addWidget(self.btn_close)
        header_vbox.addLayout(top_row)

        # Logo dinámico
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        logo_path = str(Path(__file__).parent.parent.parent / "logo_v2.png")
        if Path(logo_path).exists():
            pix = QPixmap(logo_path).scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(pix)
        else:
            self.logo_label.setText("🛡️")
            self.logo_label.setStyleSheet("font-size: 60px; color: white;")
        
        self.app_title = QLabel("VAULT CORE")
        self.app_title.setObjectName("app_title")
        self.app_title.setAlignment(Qt.AlignCenter)

        self.tagline = QLabel(MESSAGES.LOGIN.TAGLINE)
        self.tagline.setObjectName("tagline")
        self.tagline.setAlignment(Qt.AlignCenter)

        header_vbox.addWidget(self.logo_label)
        header_vbox.addSpacing(10)
        header_vbox.addWidget(self.app_title)
        header_vbox.addWidget(self.tagline)
        card_layout.addWidget(header_area)

        # --- FORM AREA ---
        form_area = QFrame()
        form_area.setObjectName("FormArea")
        form_vbox = QVBoxLayout(form_area)
        form_vbox.setContentsMargins(45, 20, 45, 30)
        form_vbox.setSpacing(15)
        
        self.welcome_label = QLabel(MESSAGES.LOGIN.WELCOME)
        self.welcome_label.setObjectName("welcome_label")
        self.welcome_label.setAlignment(Qt.AlignCenter)
        
        self.subtitle_label = QLabel(MESSAGES.LOGIN.SUBTITLE)
        self.subtitle_label.setObjectName("subtitle_label")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        
        form_vbox.addWidget(self.welcome_label)
        form_vbox.addWidget(self.subtitle_label)
        form_vbox.addSpacing(15)

        # Inputs
        self.username_input = PremiumLineEdit(MESSAGES.LOGIN.PLACEHOLDER_USER)
        self.password_input = PremiumLineEdit(MESSAGES.LOGIN.PLACEHOLDER_PWD, password=True)
        self.invitation_input = PremiumLineEdit(MESSAGES.LOGIN.PLACEHOLDER_INVITE)
        self.invitation_input.setVisible(False)

        form_vbox.addWidget(self.username_input)
        form_vbox.addWidget(self.invitation_input)
        form_vbox.addWidget(self.password_input)
        
        # Loading Progress Bar (Hidden by default)
        self.login_progress = QProgressBar()
        self.login_progress.setObjectName("login_progress")
        self.login_progress.setRange(0, 0) # Indeterminate initially
        self.login_progress.setTextVisible(False)
        self.login_progress.setFixedHeight(4)
        self.login_progress.hide()
        form_vbox.addWidget(self.login_progress)

        form_vbox.addSpacing(10)

        # Login Button
        self.login_button = QPushButton(MESSAGES.LOGIN.BTN_LOGIN)
        self.login_button.setObjectName("login_button")
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.setFixedHeight(50)
        self.login_button.clicked.connect(self.try_login)
        form_vbox.addWidget(self.login_button)

        # Links Area
        links_layout = QHBoxLayout()
        self.btn_reg_toggle = QPushButton(MESSAGES.LOGIN.REG_LINK)
        self.btn_reg_toggle.setObjectName("btn_reg_toggle")
        self.btn_reg_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_reg_toggle.clicked.connect(self._toggle_register_mode)
        
        self.btn_recovery = QPushButton(MESSAGES.RECOVERY.LINK)
        self.btn_recovery.setObjectName("btn_recovery")
        self.btn_recovery.setCursor(Qt.PointingHandCursor)
        self.btn_recovery.clicked.connect(self._show_recovery_info)
        
        links_layout.addWidget(self.btn_reg_toggle)
        links_layout.addStretch()
        links_layout.addWidget(self.btn_recovery)
        form_vbox.addLayout(links_layout)

        card_layout.addWidget(form_area)
        
        # Status Footer
        self.lbl_version = QLabel("PRO VERSION v2.2")
        self.lbl_version.setStyleSheet("color: rgba(255,255,255,0.2); font-size: 9px; font-weight: bold;")
        self.lbl_version.setAlignment(Qt.AlignCenter)
        card_layout.addStretch()
        card_layout.addWidget(self.lbl_version)
        card_layout.addSpacing(15)
        
        # Timer para el LED de conectividad
        self.conn_timer = QTimer(self)
        self.conn_timer.timeout.connect(self._check_connectivity)
        self.conn_timer.start(5000) # Cada 5 seg
        self._check_connectivity() # Primera ejecución

    def _check_connectivity(self):
        """Verifica si hay acceso a la red de forma no bloqueante."""
        try:
            import socket
            # Simple check to a reliable DNS or Supabase host
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            self.conn_led.set_state(True)
            self.conn_label.setText("SYSTEM ONLINE")
            self.conn_label.setStyleSheet("color: #00ffff; font-family: 'Consolas'; font-size: 10px; font-weight: bold;")
        except:
            self.conn_led.set_state(False)
            self.conn_label.setText("LOCAL MODE")
            self.conn_label.setStyleSheet("color: #ff5000; font-family: 'Consolas'; font-size: 10px; font-weight: bold;")

    def _apply_branding(self):
        instance_name = self.user_manager.sm.get_meta("instance_name") or "VULTRAX CORE"
        self.app_title.setText(instance_name.upper())

        if self.prefill_user:
            self.welcome_label.setText(str(MESSAGES.LOGIN.LOCKED_TITLE).upper())
            self.subtitle_label.setText(MESSAGES.LOGIN.UNLOCKING.format(user=self.prefill_user))
            self.username_input.setText(self.prefill_user)
            self.username_input.setReadOnly(True)
            self.username_input.setStyleSheet("border: 2px solid @ghost_border; border-radius: 8px; padding: 0 15px; background: rgba(30, 41, 59, 0.4); color: #64748b;")
            self.password_input.setFocus()
            
            # Hide unnecessary links in locked state
            self.btn_reg_toggle.hide()
            self.btn_recovery.hide()

    def center_on_screen(self):
        """Centra la ventana en el monitor donde se encuentre el cursor o monitor principal."""
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().screenGeometry(QDesktopWidget().cursor().pos())
        size = self.geometry()
        x = (screen.width() - size.width()) // 2 + screen.left()
        y = (screen.height() - size.height()) // 2 + screen.top()
        self.move(x, y)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def _toggle_register_mode(self):
        self.reg_mode = not self.reg_mode
        self.invitation_input.setVisible(self.reg_mode)
        
        if self.reg_mode:
            self.welcome_label.setText(MESSAGES.LOGIN.REG_WELCOME)
            self.subtitle_label.setText(MESSAGES.LOGIN.REG_SUBTITLE)
            self.login_button.setText(MESSAGES.LOGIN.BTN_REG)
            self.btn_reg_toggle.setText(MESSAGES.LOGIN.BTN_BACK_LOGIN)
            self.btn_recovery.setVisible(False)
        else:
            self.welcome_label.setText(MESSAGES.LOGIN.WELCOME)
            self.subtitle_label.setText(MESSAGES.LOGIN.SUBTITLE)
            self.login_button.setText(MESSAGES.LOGIN.BTN_LOGIN)
            self.btn_reg_toggle.setText(MESSAGES.LOGIN.REG_LINK)
            self.btn_recovery.setVisible(True)

    def _show_recovery_info(self):
        """Muestra un diálogo informativo sobre la recuperación de cuenta."""
        from src.presentation.dialogs.recovery_dialog import AccountRecoveryDialog
        dlg = AccountRecoveryDialog(self)
        dlg.exec_()

    def fade_and_close(self):
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(400)
        self.anim.setStartValue(1)
        self.anim.setEndValue(0)
        self.anim.finished.connect(self.close)
        self.anim.start()

    def try_login(self):
        try:
            # UI FEEDBACK: BARRA DE CARGA
            self.login_button.setEnabled(False)
            self.login_button.setText("VALIDATING ENCRYPTION...")
            self.login_progress.show()
            QApplication.processEvents()

            if self.reg_mode:
                u = self.username_input.text().strip().upper()
                p = self.password_input.text()
                code = self.invitation_input.text().strip().upper()
                if not u or not p or not code:
                    PremiumMessage.error(self, MESSAGES.LOGIN.TITLE_INCOMPLETE, MESSAGES.LOGIN.TEXT_INCOMPLETE)
                    self._reset_login_ui()
                    return
                success, msg = self.user_manager.register_with_invitation(code, u, p)
                if success:
                    PremiumMessage.success(self, MESSAGES.LOGIN.TITLE_REG_SUCCESS, MESSAGES.LOGIN.TEXT_REG_SUCCESS)
                    self._toggle_register_mode()
                else:
                    PremiumMessage.error(self, MESSAGES.LOGIN.TITLE_REG_FAIL, msg)
                self._reset_login_ui()
                return

            if self.locked_until and time.time() < self.locked_until:
                PremiumMessage.error(self, MESSAGES.LOGIN.TITLE_LOCKED_WAIT, MESSAGES.LOGIN.TEXT_WAIT.format(seconds=int(self.locked_until - time.time())))
                self._reset_login_ui()
                return

            u = self.username_input.text().strip()
            p = self.password_input.text()

            if not u or not p:
                PremiumMessage.info(self, MESSAGES.LOGIN.TITLE_MISSING_DATA, MESSAGES.LOGIN.TEXT_MISSING_DATA)
                self._reset_login_ui()
                return

            self.user_manager.prepare_for_user(u)
            prof = self.user_manager.validate_user_access(u)
            
            is_offline = False
            if prof is None:
                # FALLBACK OFFLINE: Si la nube no responde, intentamos local
                self.logger.warning(f"Cloud validation failed for {u}. Attempting offline fallback.")
                prof = self.user_manager.check_local_login(u, p)
                if prof and prof.get("is_offline"):
                    is_offline = True
                else:
                    # Si falla local también o no existe
                    PremiumMessage.error(self, MESSAGES.LOGIN.TITLE_INTERNAL_ERROR, "No se pudo contactar con el servidor y no hay registro local de este usuario.")
                    self._reset_login_ui()
                    return

            if not prof or not prof["exists"]:
                PremiumMessage.error(self, MESSAGES.LOGIN.TITLE_USER_NOT_FOUND, MESSAGES.LOGIN.TEXT_USER_NOT_FOUND)
                self._reset_login_ui()
                return

            if not prof.get("active", False):
                if prof.get("error") == "DEVICE_MISMATCH":
                    self.user_manager.sm.log_event("LOGIN_BLOCKED", details="Intento desde hardware no vinculado", status="FAILURE", user_name=u, user_id=prof.get("id"))
                    PremiumMessage.error(self, MESSAGES.LOGIN.TITLE_ACCESS_FORBIDDEN, 
                        MESSAGES.LOGIN.TEXT_DEVICE_MISMATCH)
                else:
                    self.user_manager.sm.log_event("LOGIN_BLOCKED", details="Intento en cuenta suspendida/inactiva", status="FAILURE", user_name=u, user_id=prof.get("id"))
                    PremiumMessage.error(self, MESSAGES.LOGIN.TITLE_ACCESS_BLOCKED, MESSAGES.LOGIN.TEXT_ACCOUNT_SUSPENDED)
                self._reset_login_ui()
                return

            # Si es offline, saltar la verificación de password (ya se hizo en check_local_login)
            if not is_offline:
                self.logger.info("[DEBUG] Calling verify_password...")
                if not self.user_manager.verify_password(p, prof["salt"], prof["password_hash"]):
                    self.logger.info("[DEBUG] Password verification FAILED.")
                    self.failed_attempts += 1
                    self.user_manager.sm.log_event("LOGIN_FAIL", details=f"Password incorrecto (Intento {self.failed_attempts})", status="FAILURE", user_name=u, user_id=prof.get("id"))
                    if self.failed_attempts >= 5: self.locked_until = time.time() + 60
                    PremiumMessage.error(self, MESSAGES.LOGIN.TITLE_ACCESS_DENIED, MESSAGES.LOGIN.TEXT_INVALID_CREDS)
                    self._reset_login_ui()
                    return
                self.logger.info("[DEBUG] Password verification SUCCESS.")

            if is_offline:
                from src.presentation.notifications.notification_manager import Notifications
                Notifications.show_toast(self, "MODO OFFLINE", "Conectado mediante caché local. Los cambios no se sincronizarán hasta detectar internet.", "🔌", "#f59e0b")

            # Login sin 2FA - Solo usuario y contraseña
            self.user_manager.sm.log_event("LOGIN_WITHOUT_2FA", details="2FA desactivado - Login solo con contraseña", user_name=u, user_id=prof.get("id"))
            sec = None

            # LOG FINAL DE EXITO
            self.user_manager.sm.log_event("LOGIN", details=f"Sesión iniciada: {u}", user_name=u, user_id=prof.get("id"))
            
            user_data = {
                "username": u, 
                "role": prof.get("role", "user"), 
                "totp_secret": sec,
                "password_hash": prof.get("password_hash"),
                "salt": prof.get("salt"),
                "vault_salt": prof.get("vault_salt"),
                "protected_key": prof.get("protected_key"),
                "wrapped_vault_key": prof.get("wrapped_vault_key"),
                "vault_id": prof.get("vault_id"),
                "vault_name": prof.get("vault_name"), 
                "id": prof.get("id")
            }
            if self.on_login_success:
                # [ANTI-DUPLICATE FIX]
                self.login_progress.setRange(0, 100)
                self.login_progress.setValue(100)
                self.login_button.setText("ACCESS GRANTED.")
                QApplication.processEvents()
                
                self.on_login_success(p, sec, user_data)
                self.fade_and_close()

        except Exception as e:
            import traceback
            self.logger.error(f"FAILED LOGIN: {e}\n{traceback.format_exc()}")
            PremiumMessage.error(self, MESSAGES.LOGIN.TITLE_INTERNAL_ERROR, str(e))
            self._reset_login_ui()

    def _reset_login_ui(self):
        """Restaura el botón y oculta la barra de progreso en caso de error."""
        self.login_button.setEnabled(True)
        self.login_button.setText(MESSAGES.LOGIN.BTN_LOGIN if not self.reg_mode else MESSAGES.LOGIN.BTN_REG)
        self.login_progress.hide()
        self.login_progress.setRange(0, 0)
