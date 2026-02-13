from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QProgressBar, QFrame, QApplication
)
from PyQt5.QtCore import Qt
from src.domain.messages import MESSAGES
from src.presentation.ui_utils import PremiumMessage
from src.presentation.theme_manager import ThemeManager
import logging

class ChangePasswordDialog(QDialog):
    def __init__(self, secrets_manager, user_manager, user_profile=None, sync_manager=None, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.sm = secrets_manager
        self.user_manager = user_manager
        self.user_profile = user_profile or {}
        self.sync_manager = sync_manager
        
        username = self.user_profile.get("username", "Global")
        self.theme = ThemeManager()
        from PyQt5.QtCore import QSettings
        self.settings = QSettings(ThemeManager.APP_ID, f"VultraxCore_{username}")
        
        active_theme = self.settings.value("theme_active", "tactical_dark")
        self.theme.set_theme(active_theme)
        
        # Fondo base instantáneo + hoja de estilos completa
        self.colors = self.theme.get_theme_colors()
        full_qss = f"QDialog {{ background-color: {self.colors['bg']}; }}\n" + self.theme.load_stylesheet("dialogs")
        self.setStyleSheet(full_qss)
        
        self.setWindowTitle(MESSAGES.DASHBOARD.CHANGE_PWD)
        self.setFixedSize(460, 680)

        self.sm = secrets_manager
        self.user_manager = user_manager
        self.user_profile = user_profile or {}
        self.sync_manager = sync_manager
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 30, 35, 30)
        layout.setSpacing(10)

        # Added a status label for sync
        self.lbl_sync_status = QLabel("")
        self.lbl_sync_status.setObjectName("dialog_subtitle")
        self.lbl_sync_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_sync_status)

        # Encabezado simple
        title = QLabel(f"🔑 {MESSAGES.DASHBOARD.CHANGE_PWD}")
        title.setObjectName("dialog_title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 1. Clave actual
        layout.addWidget(QLabel(f"{MESSAGES.LOGIN.SUBTITLE}:"))
        self.input_current = QLineEdit()
        self.input_current.setEchoMode(QLineEdit.Password)
        self.input_current.setPlaceholderText("••••••••••••")
        layout.addWidget(self.input_current)

        layout.addSpacing(10)

        # 2. Nueva clave
        layout.addWidget(QLabel(f"{MESSAGES.LOGIN.TITLE_NEW_ACCOUNT}:"))
        self.input_new = QLineEdit()
        self.input_new.setEchoMode(QLineEdit.Password)
        self.input_new.setPlaceholderText(MESSAGES.SECURITY.TEXT_MIN_LENGTH)
        self.input_new.textChanged.connect(self._update_strength)
        layout.addWidget(self.input_new)
        
        # Barra de fuerza (Simplificada)
        self.strength_bar = QProgressBar()
        self.strength_bar.setValue(0)
        self.strength_bar.setFixedHeight(6)
        layout.addWidget(self.strength_bar)
        
        self.strength_txt = QLabel(MESSAGES.DASHBOARD.get("COL_LEVEL", "Strenght") + ": ---")
        self.strength_txt.setObjectName("dialog_subtitle")
        layout.addWidget(self.strength_txt)


        layout.addWidget(QLabel(MESSAGES.LOGIN.get("TITLE_CONFIRM_PWD", "Verify") + ":"))
        self.input_confirm = QLineEdit()
        self.input_confirm.setEchoMode(QLineEdit.Password)
        self.input_confirm.setPlaceholderText("••••••••••••")
        layout.addWidget(self.input_confirm)

        layout.addSpacing(15)

        # 3. 2FA [DISABLED] - Campo oculto
        self.lbl_2fa = QLabel(MESSAGES.TWOFACTOR.LABEL_TOKEN)
        self.lbl_2fa.setVisible(False)
        layout.addWidget(self.lbl_2fa)
        self.input_2fa = QLineEdit()
        self.input_2fa.setObjectName("edit_disabled")
        self.input_2fa.setVisible(False)
        layout.addWidget(self.input_2fa)

        # 4. Barra de Progreso de Re-encriptación (NUEVO)
        self.process_bar = QProgressBar()
        self.process_bar.setRange(0, 100)
        self.process_bar.setValue(0)
        self.process_bar.setFixedHeight(12)
        self.process_bar.setTextVisible(False) # Texto lo manejamos en el label para más detalle
        self.process_bar.setVisible(False)
        layout.addWidget(self.process_bar)
        
        self.lbl_process = QLabel("")
        self.lbl_process.setObjectName("dialog_subtitle")
        self.lbl_process.setAlignment(Qt.AlignCenter)
        self.lbl_process.setVisible(False)
        layout.addWidget(self.lbl_process)

        # Botón
        self.btn_change = QPushButton(MESSAGES.COMMON.TITLE_SUCCESS.upper())
        self.btn_change.setObjectName("btn_primary")
        self.btn_change.clicked.connect(self._on_change)
        layout.addWidget(self.btn_change)

    def _update_strength(self, pwd):
        # Cálculo de fuerza
        strength = 0
        if len(pwd) >= 8: strength += 25
        if len(pwd) >= 12: strength += 25
        if any(c.isupper() for c in pwd) and any(c.islower() for c in pwd): strength += 25
        if any(c.isdigit() for c in pwd) or any(not c.isalnum() for c in pwd): strength += 25
        
        self.strength_bar.setValue(strength)
        
        if strength <= 25: color, text = self.colors["danger"], "Baja"
        elif strength <= 50: color, text = self.colors["warning"], "Media"
        elif strength <= 75: color, text = self.colors["success"], "Fuerte"
        else: color, text = self.colors["primary"], "Excelente"
            
        self.strength_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; border-radius: 3px; }}")
        self.strength_txt.setText(f"Seguridad: {text}")
        self.strength_txt.setStyleSheet(f"color: {color}; font-weight: 900;")

    def _on_change(self):
        cur = self.input_current.text().strip()
        new = self.input_new.text().strip()
        ver = self.input_confirm.text().strip()
        token = self.input_2fa.text().strip()

        # [DISABLED] 2FA no es requerido - Solo validar campos básicos
        if not cur or not new or not ver:
            PremiumMessage.info(self, MESSAGES.SECURITY.TITLE_REQUIRED, "Por favor completa todos los campos requeridos.")
            return

        if len(new) < 12:
            PremiumMessage.info(self, MESSAGES.COMMON.TITLE_INFO, MESSAGES.SECURITY.TEXT_MIN_LENGTH)
            return

        if new != ver:
            PremiumMessage.error(self, MESSAGES.SECURITY.TITLE_ERROR, MESSAGES.SECURITY.TEXT_MISMATCH)
            return

        # [DISABLED] Verificación 2FA desactivada
        # secret_2fa = self.user_profile.get("totp_secret")
        # if not secret_2fa:
        #     secret_2fa = self.user_manager.get_user_totp_secret(self.sm.current_user)
        # if secret_2fa:
        #     if not self.user_manager.verify_totp(secret_2fa, token):
        #         PremiumMessage.error(self, MESSAGES.SECURITY.TITLE_ERROR, MESSAGES.SECURITY.TEXT_2FA_WRONG)
        #         return

        try:
            # Mostrar UI de progreso
            self.lbl_process.setText("Iniciando re-encriptación segura...")
            self.process_bar.setVisible(True)
            self.process_bar.setValue(0)
            self.lbl_process.setVisible(True)
            QApplication.processEvents()

            # Callback para actualizar UI desde el loop del backend
            def progress_handler(current, total, success, errors):
                percent = int((current / total) * 100) if total > 0 else 0
                self.process_bar.setValue(percent)
                status_text = f"Procesando: {percent}% ({current}/{total})"
                if errors > 0:
                    status_text += f" | ⚠️ {errors} fallos"
                self.lbl_process.setText(status_text)
                
                # Colorear barra según estado (Usando colores del tema)
                if errors == 0:
                    self.process_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {self.colors['success']}; border-radius: 4px; }}")
                else:
                     self.process_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {self.colors['warning']}; border-radius: 4px; }}")
                
                QApplication.processEvents()

            # 1. Cambiar contraseña local y perfil en Supabase
            # SENIOR FIX: Pasamos user_manager y capturamos fallos críticos de sincronización
            # Ahora pasamos el callback de progreso
            self.sm.change_login_password(cur, new, self.user_manager, progress_callback=progress_handler)
            
            # Finalizar UI
            self.process_bar.setValue(100)
            self.lbl_process.setText("✅ Re-encriptación y sincronización completada.")
            self.lbl_process.setStyleSheet(f"color: {self.colors['success']}; font-size: 11px; margin-top: 5px;")
            
            # 2. Sincronización Automática de Secretos (NUEVO)
            if self.sync_manager:
                try:
                    self.lbl_sync_status.setText(MESSAGES.SECURITY.TEXT_SYNC_START)
                    QApplication.processEvents()
                    
                    self.sync_manager.backup_to_supabase()
                    self.lbl_sync_status.setText(MESSAGES.SECURITY.TEXT_SYNC_OK)
                except Exception as sync_err:
                    self.logger.warning(f"Auto-backup failed after password change: {sync_err}")
                    self.lbl_sync_status.setText(MESSAGES.SECURITY.TEXT_SYNC_FAIL)
                    self.lbl_sync_status.setStyleSheet("color: #fbbf24;")

            # Verificación extra: ¿El hash local ahora coincide con lo que esperamos?
            PremiumMessage.success(self, MESSAGES.SECURITY.TITLE_SUCCESS, MESSAGES.SECURITY.TEXT_SUCCESS_DETAIL)
            self.btn_change.setEnabled(True)
            self.process_bar.setVisible(False)
            self.accept()
        except Exception as e:
            self.logger.error(f"Critical error in password change: {e}")
            PremiumMessage.error(self, MESSAGES.DASHBOARD.CHANGE_PWD, f"Error: {e}")
