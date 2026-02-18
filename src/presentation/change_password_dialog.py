from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QProgressBar, QFrame, QApplication, QWidget
)
from PyQt5.QtCore import Qt
from src.domain.messages import MESSAGES
from src.presentation.ui_utils import PremiumMessage
from src.presentation.theme_manager import ThemeManager
import logging

class ChangePasswordDialog(QDialog):
    def __init__(self, secrets_manager, user_manager, user_profile=None, sync_manager=None, parent=None, target_user=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.sm = secrets_manager
        self.user_manager = user_manager
        self.user_profile = user_profile or {}
        self.sync_manager = sync_manager
        self.target_user = target_user # Si es None, es un auto-cambio. Si tiene valor, es un Admin Reset.
        
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
        self.setFixedSize(460, 720) 

        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 30, 35, 30)
        layout.setSpacing(10)

        # Status label for sync
        self.lbl_sync_status = QLabel("")
        self.lbl_sync_status.setObjectName("dialog_subtitle")
        self.lbl_sync_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_sync_status)

        # Encabezado con Identidad Dinámica
        header_text = MESSAGES.DASHBOARD.CHANGE_PWD
        if self.target_user and self.target_user.upper() != username.upper():
            # [i18n] Admin Override Title
            header_text = MESSAGES.ADMIN.get("TITLE_PROTOCOL", "ADMIN OVERRIDE").upper() + f": {self.target_user}"
            
        title = QLabel(f"🔑 {header_text}")
        title.setObjectName("dialog_title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 1. Clave de Autorización
        auth_label = MESSAGES.LOGIN.SUBTITLE
        if self.target_user and self.target_user.upper() != username.upper():
            # [i18n] Clearer Admin Auth Label
            auth_label = MESSAGES.ADMIN.get("TITLE_AUTH_L1", "ADMIN AUTHORIZATION") 
            
        layout.addWidget(QLabel(f"{auth_label}:"))
        self.input_current, self.btn_view_cur = self._create_password_field("••••••••••••")
        layout.addLayout(self._wrap_input(self.input_current, self.btn_view_cur))

        layout.addSpacing(10)

        # 2. Nueva clave
        new_label = MESSAGES.LOGIN.TITLE_NEW_ACCOUNT
        if self.target_user and self.target_user.upper() != username.upper():
            # [i18n] Specific new password label for the user
            new_label = MESSAGES.USERS.get("TITLE_RESET_PW", "NEW SIGNATURE FOR").replace("{username}", self.target_user)
            if "{username}" not in MESSAGES.USERS.get("TITLE_RESET_PW", ""):
                new_label = f"{new_label}: {self.target_user}"
            
        layout.addWidget(QLabel(f"{new_label}:"))
        self.input_new, self.btn_view_new = self._create_password_field(MESSAGES.SECURITY.TEXT_MIN_LENGTH)
        self.input_new.textChanged.connect(self._update_strength)
        layout.addLayout(self._wrap_input(self.input_new, self.btn_view_new))
        
        # Barra de fuerza
        self.strength_bar = QProgressBar()
        self.strength_bar.setValue(0)
        self.strength_bar.setFixedHeight(6)
        layout.addWidget(self.strength_bar)
        
        # [i18n] Strength label
        strength_lbl = MESSAGES.CARDS.get("SECURITY_SCORE", "Security")
        self.strength_txt = QLabel(f"{strength_lbl}: ---")
        self.strength_txt.setObjectName("dialog_subtitle")
        layout.addWidget(self.strength_txt)

        # [i18n] Confirmation label (Fixing fallback bug)
        conf_label = MESSAGES.LOGIN.get("TITLE_CONFIRM_PWD", MESSAGES.LOGIN.get("TEXT_CONFIRM_PWD", "Verify"))
        layout.addWidget(QLabel(f"{conf_label}:"))
        self.input_confirm, self.btn_view_conf = self._create_password_field("••••••••••••")
        layout.addLayout(self._wrap_input(self.input_confirm, self.btn_view_conf))

        layout.addSpacing(15)

        # 3. 2FA (Oculto)
        self.input_2fa = QLineEdit()
        self.input_2fa.setVisible(False)
        layout.addWidget(self.input_2fa)

        # 4. Barra de Progreso de Re-encriptación
        self.process_bar = QProgressBar()
        self.process_bar.setRange(0, 100)
        self.process_bar.setValue(0)
        self.process_bar.setFixedHeight(12)
        self.process_bar.setTextVisible(False)
        self.process_bar.setVisible(False)
        layout.addWidget(self.process_bar)
        
        self.lbl_process = QLabel("")
        self.lbl_process.setObjectName("dialog_subtitle")
        self.lbl_process.setAlignment(Qt.AlignCenter)
        self.lbl_process.setVisible(False)
        layout.addWidget(self.lbl_process)

        # Botón dinámico [i18n]
        btn_txt = MESSAGES.COMMON.get("BTN_YES", "EXECUTE") if self.target_user else MESSAGES.COMMON.TITLE_SUCCESS.upper()
        self.btn_change = QPushButton(btn_txt)
        self.btn_change.setObjectName("btn_primary")
        self.btn_change.clicked.connect(self._on_change)
        layout.addWidget(self.btn_change)

    def _create_password_field(self, placeholder):
        edit = QLineEdit()
        edit.setEchoMode(QLineEdit.Password)
        edit.setPlaceholderText(placeholder)
        btn = QPushButton("👁️")
        btn.setObjectName("btn_icon")
        btn.setFixedSize(35, 35)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self._toggle_visibility(edit, btn))
        return edit, btn

    def _wrap_input(self, edit, btn):
        h_layout = QHBoxLayout()
        h_layout.setSpacing(5)
        h_layout.addWidget(edit)
        h_layout.addWidget(btn)
        return h_layout

    def _toggle_visibility(self, edit, btn):
        if edit.echoMode() == QLineEdit.Password:
            edit.setEchoMode(QLineEdit.Normal)
            btn.setText("🙈")
        else:
            edit.setEchoMode(QLineEdit.Password)
            btn.setText("👁️")

    def _update_strength(self, pwd):
        strength = 0
        if len(pwd) >= 8: strength += 25
        if len(pwd) >= 12: strength += 25
        if any(c.isupper() for c in pwd) and any(c.islower() for c in pwd): strength += 25
        if any(c.isdigit() for c in pwd) or any(not c.isalnum() for c in pwd): strength += 25
        self.strength_bar.setValue(strength)
        
        # [i18n] Dynamic strength texts
        if strength <= 25: 
            color, text = self.colors["danger"], MESSAGES.SERVICE.get("STRENGTH_WEAK", "Weak")
        elif strength <= 50: 
            color, text = self.colors["warning"], MESSAGES.SERVICE.get("STRENGTH_MEDIUM", "Medium")
        elif strength <= 75: 
            color, text = self.colors["success"], MESSAGES.SERVICE.get("STRENGTH_STRONG", "Strong")
        else: 
            color, text = self.colors["primary"], MESSAGES.SERVICE.get("STRENGTH_SECURE", "Excellent")
            
        self.strength_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; border-radius: 3px; }}")
        
        strength_lbl = MESSAGES.CARDS.get("SECURITY_SCORE", "Security")
        self.strength_txt.setText(f"{strength_lbl}: {text}")
        self.strength_txt.setStyleSheet(f"color: {color}; font-weight: 900;")

    def _on_change(self):
        auth_pwd = self.input_current.text().strip()
        new_pwd = self.input_new.text().strip()
        ver_pwd = self.input_confirm.text().strip()

        # [i18n] Error handling
        if not auth_pwd or not new_pwd or not ver_pwd:
            PremiumMessage.info(self, MESSAGES.SECURITY.TITLE_REQUIRED, MESSAGES.LOGIN.get("TEXT_INCOMPLETE", "Complete all signatures."))
            return

        if len(new_pwd) < 12:
            PremiumMessage.info(self, MESSAGES.COMMON.TITLE_INFO, MESSAGES.SECURITY.TEXT_MIN_LENGTH)
            return

        if new_pwd != ver_pwd:
            PremiumMessage.error(self, MESSAGES.SECURITY.TITLE_ERROR, MESSAGES.SECURITY.TEXT_MISMATCH)
            return

        try:
            self.lbl_process.setText("Iniciando motor de re-encriptación...")
            self.process_bar.setVisible(True)
            self.process_bar.setValue(0)
            self.lbl_process.setVisible(True)
            QApplication.processEvents()

            def progress_handler(current, total, success, errors):
                percent = int((current / total) * 100) if total > 0 else 0
                self.process_bar.setValue(percent)
                status_text = f"Procesando: {percent}% ({current}/{total})"
                if errors > 0: status_text += f" | ⚠️ {errors} fallos"
                self.lbl_process.setText(status_text)
                color = self.colors['success'] if errors == 0 else self.colors['warning']
                self.process_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; border-radius: 4px; }}")
                QApplication.processEvents()

            # --- EJECUCIÓN DEL MODO SELECCIONADO ---
            if self.target_user and self.target_user.upper() != self.user_profile.get("username", "").upper():
                # MODO ADMIN OVERRIDE (Reset de otro usuario)
                # Primero validamos la clave del admin
                admin_name = self.user_profile.get("username", "Global")
                is_valid = self.user_manager.verify_password(
                    auth_pwd, 
                    self.user_manager.sm.get_local_user_profile(admin_name)["salt"],
                    self.user_manager.sm.get_local_user_profile(admin_name)["password_hash"]
                )
                if not is_valid:
                    PremiumMessage.error(self, MESSAGES.ADMIN.MSG_DENIED, MESSAGES.ADMIN.TEXT_DENIED)
                    self.process_bar.setVisible(False); self.lbl_process.setVisible(False)
                    return

                # Ejecutar Reset de Identidad Administrativo
                self.sm.admin_reset_user_identity(
                    self.target_user, 
                    new_pwd, 
                    self.user_manager, 
                    progress_callback=lambda c, t, s, e: progress_handler(c, t, s, e)
                )
            else:
                # MODO AUTO-CAMBIO (El usuario cambia su propia clave)
                self.sm.change_login_password(auth_pwd, new_pwd, self.user_manager, progress_callback=progress_handler)
            
            self.process_bar.setValue(100)
            self.lbl_process.setText("✅ Operación completada con integridad nuclear.")
            
            if self.sync_manager:
                try: self.sync_manager.backup_to_supabase()
                except Exception as e:
                    self.logger.debug(f"Cloud backup failed after password rotation: {e}")

            PremiumMessage.success(self, MESSAGES.SECURITY.TITLE_SUCCESS, "La Firma Maestra ha sido rotada exitosamente.")
            self.accept()
        except Exception as e:
            self.logger.error(f"Error in unified password change: {e}")
            PremiumMessage.error(self, MESSAGES.DASHBOARD.CHANGE_PWD, f"Fallo Crítico: {e}")
            self.process_bar.setVisible(False); self.lbl_process.setVisible(False)
