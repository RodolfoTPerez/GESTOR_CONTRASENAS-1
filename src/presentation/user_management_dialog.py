from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QLineEdit, QLabel, 
    QComboBox, QHeaderView, QFrame, QAbstractItemView, QInputDialog, QWidget, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from src.domain.messages import MESSAGES
from src.presentation.ui_utils import PremiumMessage
from src.presentation.theme_manager import ThemeManager
from src.presentation.change_password_dialog import ChangePasswordDialog

class UserManagementDialog(QDialog):
    def __init__(self, user_manager, current_username, parent=None):
        super().__init__(parent)
        
        # [ESTRATEGIA TOTAL]
        # 1. Congelar pintura
        self.setUpdatesEnabled(False)
        self.setWindowOpacity(0.0) # Invisible al inicio
        
        # 2. Atributos de pintura profunda
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        
        # 3. Forzar Modo Oscuro en Windows (Nivel Hardware/SO)
        try:
            from ctypes import windll, c_int, byref, sizeof
            HWND = int(self.winId())
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            state = c_int(1)
            windll.dwmapi.DwmSetWindowAttribute(HWND, DWMWA_USE_IMMERSIVE_DARK_MODE, byref(state), sizeof(state))
        except Exception: 
            pass # No-op en otros SO
            
        self.user_manager = user_manager
        self.admin_name = current_username
        self.setWindowTitle(MESSAGES.USERS.TITLE_WINDOW)
        self.setFixedSize(1150, 700) 
        
        from PyQt5.QtCore import QSettings
        if current_username:
             self.settings = QSettings(ThemeManager.APP_ID, f"VultraxCore_{current_username}")
        else:
             self.settings = QSettings(ThemeManager.APP_ID, "VultraxCore_Global")
        
        self.theme = ThemeManager()
        active_theme = self.settings.value("theme_active", "tactical_dark")
        self.theme.set_theme(active_theme)
        colors = self.theme.get_theme_colors()

        # [SOLUCIÓN DEL USUARIO 1] Fondo oscuro HARDCODED inmediato 
        # (Sin esperar a que cargue el QSS externo)
        bg_hex = colors.get('bg', '#050505')
        
        # [SOLUCIÓN COMBINADA] Aplicamos opacidad mínima y fondo forzado
        self.setStyleSheet(f"QDialog {{ background-color: {bg_hex}; }}")
        
        # Cargar QSS completo asegurando que el fondo persista
        full_qss = self.theme.load_stylesheet("dialogs")
        self.setStyleSheet(f"QDialog {{ background-color: {bg_hex} !important; }}\n{full_qss}")

        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents() # Procesar para que el estilo se asiente

        # [THEME FIX] Wrapper Strategy for Windows Dialogs
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.frame = QFrame()
        self.frame.setObjectName("DialogFrame")
        self.frame.setAttribute(Qt.WA_StyledBackground, True)
        self.main_layout.addWidget(self.frame)
        
        # [CRITICAL] Force background on the Frame via Property/QSS
        # Removed manual inline style to rely on QSS rules
        # colors = self.theme.get_theme_colors()
        # self.frame.setStyleSheet(f"QFrame {{ background-color: {colors['bg']}; }}")

        layout = QVBoxLayout(self.frame)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # Título y contador
        header_layout = QHBoxLayout()
        self.lbl_title = QLabel(MESSAGES.USERS.HEADER)
        self.lbl_title.setObjectName("dialog_title")
        header_layout.addWidget(self.lbl_title)
        
        header_layout.addStretch()
        
        self.lbl_count = QLabel("Usuarios registrados: 0 / 5")
        self.lbl_count.setObjectName("dialog_subtitle")
        header_layout.addWidget(self.lbl_count)
        layout.addLayout(header_layout)

        # CUERPO PRINCIPAL HORIZONTAL
        main_h_layout = QHBoxLayout()
        main_h_layout.setSpacing(20)

        # --- COLUMNA IZQUIERDA: GESTIÓN DE USUARIOS ---
        left_column = QVBoxLayout()
        
        self.table = QTableWidget(0, 7) 
        self.table.setHorizontalHeaderLabels([
            MESSAGES.USERS.COL_USER, MESSAGES.USERS.COL_ROLE, MESSAGES.USERS.COL_STATUS, 
            MESSAGES.USERS.COL_2FA, MESSAGES.USERS.COL_ACTION, MESSAGES.USERS.COL_KEY, MESSAGES.USERS.COL_DEL
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(50)  # Set row height for vertical centering
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setMinimumWidth(650)
        self.table.cellClicked.connect(self._on_table_cell_clicked)  # Handle emoji clicks
        left_column.addWidget(self.table)
        
        # --- SECCIÓN INVITACIONES ---
        inv_frame = QFrame()
        inv_frame.setObjectName("card")
        inv_layout = QVBoxLayout(inv_frame)
        
        inv_header = QHBoxLayout()
        inv_header.addWidget(QLabel(MESSAGES.USERS.TITLE_INVITES))
        inv_header.addStretch()
        self.btn_invite = QPushButton(MESSAGES.USERS.BTN_GEN_INVITE)
        self.btn_invite.setObjectName("btn_primary")
        self.btn_invite.clicked.connect(self._on_create_invite)
        inv_header.addWidget(self.btn_invite)
        inv_layout.addLayout(inv_header)
        
        self.inv_table = QTableWidget(0, 3)
        self.inv_table.setHorizontalHeaderLabels([MESSAGES.USERS.COL_CODE, MESSAGES.USERS.COL_ROLE, MESSAGES.USERS.COL_CREATED_BY])
        self.inv_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.inv_table.verticalHeader().setVisible(False)
        self.inv_table.setMaximumHeight(150)
        inv_layout.addWidget(self.inv_table)
        
        left_column.addWidget(inv_frame)
        main_h_layout.addLayout(left_column, stretch=3)

        # --- COLUMNA DERECHA: FORMULARIO AGREGAR ---
        right_column = QVBoxLayout()
        
        form_frame = QFrame()
        form_frame.setFixedWidth(280)
        form_frame.setObjectName("card")
        form_layout = QVBoxLayout(form_frame)
        
        form_layout.addWidget(QLabel(MESSAGES.USERS.LBL_NEW_USER))
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText(MESSAGES.USERS.PH_NAME)
        form_layout.addWidget(self.input_name)

        form_layout.addWidget(QLabel(MESSAGES.USERS.LBL_ROLE))
        self.combo_role = QComboBox()
        self.combo_role.addItems(["user", "admin"])
        form_layout.addWidget(self.combo_role)

        form_layout.addWidget(QLabel(MESSAGES.USERS.LBL_MASTER_PWD))
        
        # Password field with visibility toggle
        pwd_container = QHBoxLayout()
        pwd_container.setSpacing(0)
        
        self.input_pwd = QLineEdit()
        self.input_pwd.setPlaceholderText(MESSAGES.USERS.PH_PWD)
        self.input_pwd.setEchoMode(QLineEdit.Password)
        pwd_container.addWidget(self.input_pwd)
        
        # Toggle visibility button
        self.btn_toggle_pwd = QPushButton("👁️")
        self.btn_toggle_pwd.setObjectName("btn_icon")
        self.btn_toggle_pwd.setFixedSize(40, 40)
        self.btn_toggle_pwd.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_pwd.setToolTip("Show/Hide Password")
        self.btn_toggle_pwd.clicked.connect(self._toggle_password_visibility)
        pwd_container.addWidget(self.btn_toggle_pwd)
        
        form_layout.addLayout(pwd_container)
        
        # Strength Meter
        strength_container = QVBoxLayout()
        strength_container.setSpacing(2)
        
        self.strength_bar = QProgressBar()
        self.strength_bar.setRange(0, 100)
        self.strength_bar.setValue(0)
        self.strength_bar.setTextVisible(False)
        self.strength_bar.setFixedHeight(6)
        self.strength_bar.setStyleSheet("QProgressBar { background-color: #334155; border-radius: 3px; border: none; }")
        strength_container.addWidget(self.strength_bar)
        
        self.strength_label = QLabel("Strength: -")
        self.strength_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; margin-top: 2px;")
        self.strength_label.setAlignment(Qt.AlignRight)
        strength_container.addWidget(self.strength_label)
        
        form_layout.addLayout(strength_container)
        
        # Connect signal
        self.input_pwd.textChanged.connect(self._update_strength_meter)
        
        form_layout.addSpacing(10)

        self.btn_add = QPushButton(MESSAGES.USERS.BTN_ADD)
        self.btn_add.setObjectName("btn_primary")
        self.btn_add.setMinimumHeight(45)
        self.btn_add.clicked.connect(self._on_add_user)
        form_layout.addWidget(self.btn_add)
        
        form_layout.addStretch()
        
        help_lbl = QLabel(MESSAGES.USERS.LBL_LIMIT_NOTE)
        help_lbl.setWordWrap(True)
        help_lbl.setObjectName("dialog_subtitle")
        form_layout.addWidget(help_lbl)

        right_column.addWidget(form_frame)
        main_h_layout.addLayout(right_column, stretch=1)

        layout.addLayout(main_h_layout)
        
        # Cargar datos iniciales
        self._refresh_data()

        # [REVEAL] Reactivar y mostrar suavemente
        self.setUpdatesEnabled(True)
        from PyQt5.QtCore import QTimer
        # 150ms es el tiempo ideal para que el hardware de Windows aplique el DWM attribute
        QTimer.singleShot(150, lambda: self.setWindowOpacity(1.0))

    def _toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.input_pwd.echoMode() == QLineEdit.Password:
            self.input_pwd.setEchoMode(QLineEdit.Normal)
            self.btn_toggle_pwd.setText("🙈")  # Hide icon
        else:
            self.input_pwd.setEchoMode(QLineEdit.Password)
            self.btn_toggle_pwd.setText("👁️")  # Show icon

    def _update_strength_meter(self):
        """Analyze password strength and update UI"""
        pwd = self.input_pwd.text()
        score = 0
        
        # Length points
        if len(pwd) >= 16: score += 40
        elif len(pwd) >= 12: score += 30
        elif len(pwd) >= 8: score += 15
        
        # Complexity points
        if any(c.islower() for c in pwd) and any(c.isupper() for c in pwd): score += 20
        if any(c.isdigit() for c in pwd): score += 20
        if any(c in "!@#$%^&*()-_=+[]{}<>?/|\\;:.,~" for c in pwd): score += 20
        
        score = min(100, score)
        self.strength_bar.setValue(score)
        
        level = "weak"
        text = "WEAK"
        if score < 40: level, text = "weak", "WEAK 🔴"
        elif score < 75: level, text = "medium", "MEDIUM 🟡"
        elif score < 95: level, text = "strong", "STRONG 🟢"
        else: level, text = "secure", "SECURE 🛡️"

        # Apply style property for QSS
        self.strength_bar.setProperty("strength_level", level)
        self.strength_label.setProperty("strength_level", level)
        self.strength_label.setText(text)
        
        # Force refresh style
        self.strength_bar.style().unpolish(self.strength_bar)
        self.strength_bar.style().polish(self.strength_bar)
        
        self.strength_label.style().unpolish(self.strength_label)
        self.strength_label.style().polish(self.strength_label)

    def _on_table_cell_clicked(self, row, col):
        """Handle clicks on emoji cells"""
        if col < 3 or row >= self.table.rowCount():
            return
            
        # Get username and user data
        username_item = self.table.item(row, 0)
        if not username_item:
            return
        username = username_item.text()
        
        # Find user data
        users = self.user_manager.get_all_users()
        user_data = next((u for u in users if u.get('username') == username), None)
        if not user_data:
            return
        
        # Execute action based on column
        if col == 3:  # 2FA
            self._on_reset_2fa(username)
        elif col == 4:  # Toggle Status
            self._on_toggle_user(user_data['id'], user_data.get('active', False), user_data.get('role', 'user'), username)
        elif col == 5:  # Reset Password
            self._on_reset_password(username)
        elif col == 6:  # Delete
            self._on_delete_user(user_data['id'], username, user_data.get('role', 'user'))

    def _create_centered_button(self, icon, tooltip, callback, danger=False):
        """Helper to create a centered icon button"""
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        
        btn = QPushButton(icon)
        btn.setObjectName("btn_icon_danger" if danger else "btn_icon")
        btn.setToolTip(tooltip)
        btn.setFixedSize(32, 32)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(callback)
        
        layout.addWidget(btn)
        return container

    def _on_create_invite(self):
        role, ok = QInputDialog.getItem(self, MESSAGES.USERS.TITLE_NEW_INVITE, MESSAGES.USERS.TEXT_ROLE_INVITE, ["user", "admin"], 0, False)
        if ok:
            success, code = self.user_manager.create_invitation(role, self.admin_name)
            if success:
                PremiumMessage.success(self, MESSAGES.USERS.TITLE_INVITE_CREATED, MESSAGES.USERS.TEXT_INVITE_CREATED.format(code=code))
                self._refresh_data()
            else:
                PremiumMessage.error(self, MESSAGES.COMMON.TITLE_ERROR, code)

    def _refresh_data(self):
        users = self.user_manager.get_all_users()
        count = len(users)
        self.lbl_count.setText(MESSAGES.USERS.LBL_COUNT.format(current=count, max=5))
        
        # INCREASED COLUMN COUNT FOR 2FA RESET
        self.table.setColumnCount(7) 
        self.table.setHorizontalHeaderLabels([
            MESSAGES.USERS.COL_USER, MESSAGES.USERS.COL_ROLE, MESSAGES.USERS.COL_STATUS, 
            MESSAGES.USERS.COL_2FA, MESSAGES.USERS.COL_ACTION, MESSAGES.USERS.COL_KEY, MESSAGES.USERS.COL_DEL
        ])
        self.table.setRowCount(count)
        
        for i, u in enumerate(users):
            # Username
            name_item = QTableWidgetItem(u.get("username", "---"))
            name_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 0, name_item)
            
            
            # Role
            role_item = QTableWidgetItem(u.get("role", "user"))
            role_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 1, role_item)
            
            # Status - ONLY emoji, no text
            is_active = u.get("active", False)
            status_emoji = "✅" if is_active else "🚫"
            status_item = QTableWidgetItem(status_emoji)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 2, status_item)
            
            # Centered emoji items (clickable via cellClicked signal)
            item_2fa = QTableWidgetItem("🔒")
            item_2fa.setTextAlignment(Qt.AlignCenter)
            item_2fa.setToolTip("Reset 2FA")
            self.table.setItem(i, 3, item_2fa)
            
            toggle_icon = "✅" if is_active else "🚫"
            item_toggle = QTableWidgetItem(toggle_icon)
            item_toggle.setTextAlignment(Qt.AlignCenter)
            item_toggle.setToolTip("Suspend" if is_active else "Activate")
            self.table.setItem(i, 4, item_toggle)
            
            item_reset = QTableWidgetItem("🔑")
            item_reset.setTextAlignment(Qt.AlignCenter)
            item_reset.setToolTip("Reset Password")
            self.table.setItem(i, 5, item_reset)
            
            item_del = QTableWidgetItem("🔥")
            item_del.setTextAlignment(Qt.AlignCenter)
            item_del.setToolTip("Delete User")
            self.table.setItem(i, 6, item_del)
            
        # Deshabilitar botón si llegamos al límite
        self.btn_add.setEnabled(count < 5)
        if count >= 5:
            self.btn_add.setText(MESSAGES.USERS.BTN_LIMIT)
            self.btn_add.setStyleSheet("background-color: #4b5563; color: white;")
        else:
            self.btn_add.setText(MESSAGES.USERS.BTN_ADD_FULL)
            self.btn_add.setStyleSheet("")

        # REFRESCAR INVITACIONES
        invs = self.user_manager.get_invitations()
        self.inv_table.setRowCount(len(invs))
        if self.inv_table.columnCount() < 4:
            self.inv_table.setColumnCount(4)
            self.inv_table.setHorizontalHeaderLabels([
                MESSAGES.USERS.COL_CODE, MESSAGES.USERS.COL_ROLE, 
                MESSAGES.USERS.COL_CREATED_BY, MESSAGES.USERS.COL_STATUS
            ])

        for i, inv in enumerate(invs):
            is_used = inv.get("used", False)
            
            code_item = QTableWidgetItem(inv.get("code", "---"))
            code_item.setForeground(QColor("#00FF00") if not is_used else QColor("#888888"))
            code_item.setTextAlignment(Qt.AlignCenter)
            self.inv_table.setItem(i, 0, code_item)
            
            role_item = QTableWidgetItem(inv.get("role", "user"))
            role_item.setTextAlignment(Qt.AlignCenter)
            self.inv_table.setItem(i, 1, role_item)
            
            creator_item = QTableWidgetItem(inv.get("created_by", "SYSTEM"))
            creator_item.setTextAlignment(Qt.AlignCenter)
            self.inv_table.setItem(i, 2, creator_item)

            status_text = "ACTIVE" if not is_used else "USED"
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            if not is_used:
                status_item.setForeground(QColor("#FFFF00")) # Yellow for active
            else:
                status_item.setForeground(QColor("#FF4444")) # Red for used
            self.inv_table.setItem(i, 3, status_item)

    def _on_reset_2fa(self, username):
        """Permite al admin eliminar el secreto 2FA dañado de un usuario."""
        if PremiumMessage.question(self, MESSAGES.USERS.TITLE_CONFIRM_2FA, MESSAGES.USERS.TEXT_CONFIRM_2FA.format(username=username)):
            try:
                # Direct update to clear totp_secret
                self.user_manager.supabase.table("users").update({"totp_secret": None}).eq("username", username).execute()
                PremiumMessage.success(self, MESSAGES.USERS.TITLE_2FA_RESET, MESSAGES.USERS.TEXT_2FA_RESET.format(username=username))
            except Exception as e:
                PremiumMessage.error(self, MESSAGES.COMMON.TITLE_ERROR, f"{e}")

    def _on_add_user(self):
        name = self.input_name.text().strip()
        role = self.combo_role.currentText()
        pwd = self.input_pwd.text().strip()
        
        if not name or not pwd:
            PremiumMessage.info(self, MESSAGES.USERS.TITLE_ERROR, MESSAGES.USERS.TEXT_REQ_FIELDS)
            return

        if len(pwd) < 8:
            PremiumMessage.error(self, MESSAGES.USERS.TITLE_ERROR, MESSAGES.USERS.TEXT_MIN_PWD)
            return

        success, msg = self.user_manager.add_new_user(name, role, pwd)
        
        # [SECURITY] Secure password clearing from memory
        pwd = None  # Dereference
        self.input_pwd.setText("X" * 32)  # Overwrite with dummy data
        self.input_pwd.clear()  # Clear field
        
        if success:
            PremiumMessage.success(self, MESSAGES.USERS.TITLE_SUCCESS, MESSAGES.USERS.TEXT_USER_CREATED)
            self.input_name.clear()
            self._refresh_data()
        else:
            PremiumMessage.error(self, MESSAGES.USERS.TITLE_ERROR, msg)

    def _on_toggle_user(self, user_id, current_status, role, username):
        if role == "admin":
            PremiumMessage.error(self, MESSAGES.USERS.TITLE_FORBIDDEN, MESSAGES.USERS.TEXT_NO_DELETE_ADMIN)
            return

        action = "suspend" if current_status else "activate"
        if PremiumMessage.question(self, "Change Status", f"Are you sure you want to {action} user {username}?"):
            success, msg = self.user_manager.toggle_user_status(user_id, current_status)
            if success:
                PremiumMessage.success(self, MESSAGES.USERS.TITLE_SUCCESS, f"User {username} {action}ed successfully.")
                self._refresh_data()
            else:
                PremiumMessage.error(self, MESSAGES.USERS.TITLE_ERROR, msg)

    def _on_reset_password(self, username):
        """
        Permite al admin resetear la clave maestra de un usuario.
        [UNIFIED ARCHITECTURE]: Usa el motor ChangePasswordDialog para TODO.
        """
        if not self.user_manager.sm or not self.user_manager.sm.master_key:
             PremiumMessage.error(self, MESSAGES.USERS.TITLE_SEC_ERROR, MESSAGES.USERS.TEXT_SEC_ERROR)
             return

        # Obtener perfiles para el motor
        admin_profile = self.user_manager.sm.get_local_user_profile(self.admin_name)
        
        # Lanzar el Diálogo Premium Unificado
        # Si username == admin_name, target_user será el admin (Auto-reset)
        # Si no, target_user será el tercero (Admin Override)
        dlg = ChangePasswordDialog(
            self.user_manager.sm, 
            self.user_manager, 
            admin_profile, 
            None, 
            self,
            target_user=username
        )
        
        # Efecto de transparencia táctica
        dlg.setWindowOpacity(0.98)
        
        if dlg.exec_() == QDialog.Accepted:
            self._refresh_data()

    def _on_delete_user(self, user_id, username, role):
        if role == "admin":
            PremiumMessage.error(self, MESSAGES.USERS.TITLE_FORBIDDEN, MESSAGES.USERS.TEXT_NO_DELETE_ADMIN)
            return

        if PremiumMessage.question(self, MESSAGES.USERS.TITLE_DELETE_CONFIRM, MESSAGES.USERS.TEXT_CONFIRM_DELETE.format(username=username)):
            success, msg = self.user_manager.delete_user(user_id)
            if success:
                PremiumMessage.success(self, MESSAGES.USERS.TITLE_SUCCESS, msg)
                self._refresh_data()
            else:
                # Si falló por Protocolo Activo, ofrecer FUERZA BRUTA
                if "PROTOCOLO ACTIVO" in msg or "ACTIVE PROTOCOL" in msg:
                    if PremiumMessage.question(self, MESSAGES.USERS.TITLE_FORCE_DEL, MESSAGES.USERS.TEXT_FORCE_DEL.format(error=msg)):
                        
                        s2, m2 = self.user_manager.delete_user(user_id, force=True)
                        if s2:
                            PremiumMessage.success(self, MESSAGES.USERS.TITLE_FORCED, MESSAGES.USERS.TEXT_FORCED.format(username=username))
                            self._refresh_data()
                        else:
                            PremiumMessage.error(self, MESSAGES.USERS.TITLE_FATAL, m2)
                else:
                    PremiumMessage.error(self, MESSAGES.USERS.TITLE_ERROR, msg)
