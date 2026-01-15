print(">>> DASHBOARD_VIEW CARGADO DESDE:", __file__)

import secrets
import string
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QLabel,
    QMessageBox, QProgressBar, QToolButton, QSlider,
    QCheckBox, QRadioButton, QButtonGroup, QApplication,
    QDialog, QTextEdit, QDialogButtonBox, QFrame
)
from PyQt5.QtCore import (
    QTimer, QEvent, Qt, QPropertyAnimation, QEasingCurve
)
from PyQt5.QtGui import QColor

INACTIVITY_LIMIT_MS = 5 * 60 * 1000  # 5 minutos


# ============================================================
#   SWITCH MODERNO PARA CAMBIAR ENTRE LIGHT / DARK MODE
# ============================================================
class ToggleSwitch(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setMinimumWidth(50)
        self.setMaximumWidth(50)
        self.setMinimumHeight(24)
        self.setCursor(Qt.PointingHandCursor)
        self.update_style()
        self.toggled.connect(self.update_style)

    def update_style(self):
        if self.isChecked():
            self.setStyleSheet("""
                QPushButton {
                    background-color: #2d7dca;
                    border-radius: 12px;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #555;
                    border-radius: 12px;
                }
            """)

    def paintEvent(self, event):
        super().paintEvent(event)
        from PyQt5.QtGui import QPainter, QColor as _QColor

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        radius = 20
        margin = 2

        if self.isChecked():
            x = self.width() - radius - margin
            color = _QColor("#ffffff")
        else:
            x = margin
            color = _QColor("#dddddd")

        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(x, margin, radius, radius)


# ============================================================
#   DIALOGO MODERNO (AGREGAR / EDITAR SERVICIO)
# ============================================================
class ServiceDialog(QDialog):
    def __init__(self, parent=None, title="Servicio", record=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.record = record or {}

        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(420)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title_label)

        lbl_service = QLabel("Servicio")
        self.edit_service = QLineEdit()
        main_layout.addWidget(lbl_service)
        main_layout.addWidget(self.edit_service)

        lbl_user = QLabel("Usuario")
        self.edit_user = QLineEdit()
        main_layout.addWidget(lbl_user)
        main_layout.addWidget(self.edit_user)

        lbl_pwd = QLabel("Contraseña")
        main_layout.addWidget(lbl_pwd)

        pwd_row = QHBoxLayout()

        self.edit_password = QLineEdit()
        self.edit_password.setEchoMode(QLineEdit.Password)
        self.edit_password.textChanged.connect(self._update_strength_meter)
        pwd_row.addWidget(self.edit_password)

        self.btn_toggle_pwd = QToolButton()
        self.btn_toggle_pwd.setText("👁️")
        self.btn_toggle_pwd.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_pwd.setStyleSheet("border: none; padding: 0px;")
        self.btn_toggle_pwd.clicked.connect(self._toggle_pwd_visibility)
        pwd_row.addWidget(self.btn_toggle_pwd)

        self.btn_generate = QPushButton("Generar segura")
        self.btn_generate.setCursor(Qt.PointingHandCursor)
        self.btn_generate.clicked.connect(self._generate_password)
        pwd_row.addWidget(self.btn_generate)

        main_layout.addLayout(pwd_row)

        self.strength_bar = QProgressBar()
        self.strength_bar.setRange(0, 100)
        self.strength_bar.setValue(0)
        self.strength_bar.setTextVisible(False)
        self.strength_bar.setFixedHeight(8)
        self.strength_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 4px;
                background: #eee;
            }
            QProgressBar::chunk {
                border-radius: 4px;
                background-color: red;
            }
        """)
        main_layout.addWidget(self.strength_bar)

        self.strength_label = QLabel("Fortaleza: -")
        self.strength_label.setStyleSheet("font-size: 12px;")
        main_layout.addWidget(self.strength_label)

        lbl_notes = QLabel("Notas / Observaciones")
        self.edit_notes = QTextEdit()
        self.edit_notes.setFixedHeight(120)
        main_layout.addWidget(lbl_notes)
        main_layout.addWidget(self.edit_notes)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        if record:
            self.edit_service.setText(record.get("service", ""))
            self.edit_user.setText(record.get("username", ""))
            self.edit_password.setText(record.get("secret", ""))
            self.edit_notes.setPlainText(record.get("notes", "") or "")
            self._update_strength_meter()

    def _toggle_pwd_visibility(self):
        if self.edit_password.echoMode() == QLineEdit.Password:
            self.edit_password.setEchoMode(QLineEdit.Normal)
            self.btn_toggle_pwd.setText("🙈")
        else:
            self.edit_password.setEchoMode(QLineEdit.Password)
            self.btn_toggle_pwd.setText("👁️")

    def _generate_password(self):
        chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
        pwd = "".join(secrets.choice(chars) for _ in range(16))
        self.edit_password.setText(pwd)
        self._update_strength_meter()

    def _update_strength_meter(self):
        pwd = self.edit_password.text()
        score = 0

        if len(pwd) >= 8: score += 20
        if len(pwd) >= 12: score += 20
        if any(c.islower() for c in pwd): score += 20
        if any(c.isupper() for c in pwd): score += 20
        if any(c.isdigit() for c in pwd): score += 10
        if any(c in "!@#$%^&*()-_=+" for c in pwd): score += 10

        self.strength_bar.setValue(score)

        if score < 40:
            color = "red"
            text = "Débil"
        elif score < 70:
            color = "orange"
            text = "Media"
        else:
            color = "green"
            text = "Fuerte"

        self.strength_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #ccc;
                border-radius: 4px;
                background: #eee;
            }}
            QProgressBar::chunk {{
                border-radius: 4px;
                background-color: {color};
            }}
        """)
        self.strength_label.setText(f"Fortaleza: {text}")

    def get_data(self):
        return {
            "service": self.edit_service.text().strip(),
            "username": self.edit_user.text().strip(),
            "secret": self.edit_password.text().strip(),
            "notes": self.edit_notes.toPlainText().strip()
        }


class TotpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Verificación 2FA")
        self.setModal(True)

        layout = QVBoxLayout(self)

        label = QLabel("Ingrese su token 2FA (TOTP):")
        self.input = QLineEdit()
        self.input.setEchoMode(QLineEdit.Normal)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(label)
        layout.addWidget(self.input)
        layout.addWidget(buttons)

    def get_token(self):
        return self.input.text().strip()


# ============================================================
#   DASHBOARD PRINCIPAL
# ============================================================
class DashboardView(QWidget):
    def __init__(self, sm, sync_manager, user_manager):
        super().__init__()
        self.sm = sm
        self.sync_manager = sync_manager
        self.user_manager = user_manager

        self.setWindowTitle("PassGuardian")
        self.setMinimumSize(1100, 650)

        self._build_ui()
        self._load_table()
        self._start_clock()

        self.internet_online = False
        self.syncing_active = False
        self.supabase_anim_active = False

        self.internet_frames = ["🌐🟢 Conectado", "🌐🟢 Conectado", "🌐🟢 Conectado"]
        self.internet_frame_index = 0

        self.sync_frames = ["⬆️⬇️ Sync...", "⬆️⬇️ Sync..", "⬆️⬇️ Sync."]
        self.sync_frame_index = 0

        self.supabase_frames = ["Supabase: 🟢 Online", "Supabase: 🟢 Online", "Supabase: 🟢 Online"]
        self.supabase_frame_index = 0

        self.inactivity_timer = QTimer()
        self.inactivity_timer.setInterval(INACTIVITY_LIMIT_MS)
        self.inactivity_timer.timeout.connect(self.lock_app)

        self.internet_anim_timer = QTimer()
        self.internet_anim_timer.timeout.connect(self._animate_internet)
        self.internet_anim_timer.start(500)

        self.sync_anim_timer = QTimer()
        self.sync_anim_timer.timeout.connect(self._animate_sync)

        self.supabase_anim_timer = QTimer()
        self.supabase_anim_timer.timeout.connect(self._animate_supabase)

        self.internet_check_timer = QTimer()
        self.internet_check_timer.timeout.connect(self._update_internet_realtime)
        self.internet_check_timer.start(3000)

        self.supabase_check_timer = QTimer()
        self.supabase_check_timer.timeout.connect(self._update_supabase_realtime)
        self.supabase_check_timer.start(5000)

        self.sqlite_check_timer = QTimer()
        self.sqlite_check_timer.timeout.connect(self._update_sqlite_realtime)
        self.sqlite_check_timer.start(7000)

        self.installEventFilter(self)


 

    # ============================================================
    #   EVENTOS DE ACTIVIDAD (AUTO-LOCK)
    # ============================================================
    def eventFilter(self, obj, event):
        if event.type() in (
            QEvent.MouseMove,
            QEvent.MouseButtonPress,
            QEvent.KeyPress,
            QEvent.Wheel
        ):
            if hasattr(self, "inactivity_timer"):
                self.inactivity_timer.start()
        return super().eventFilter(obj, event)

    def lock_app(self):
        try:
            print(">>> Auto-lock activado")
            if hasattr(self, "inactivity_timer"):
                self.inactivity_timer.stop()
            self.hide()

            from src.presentation.login_view import LoginView

            def on_login_success(master_password, totp_secret):
                print(">>> Login correcto, desbloqueando dashboard")
                self.show()

            self.login_view = LoginView(on_login_success)
            self.login_view.show()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # ============================================================
    #   UI PRINCIPAL ORIGINAL (NO SE TOCA)
    # ============================================================
    def _build_ui(self):
        main_layout = QHBoxLayout(self)

        # ========= LADO IZQUIERDO =========
        left_layout = QVBoxLayout()

        # ---- Botones ----
        btn_layout = QHBoxLayout()

        btn_add = QPushButton("Agregar servicio")
        btn_add.clicked.connect(self._on_add)

        btn_generate_simple = QPushButton("Generar segura")
        btn_generate_simple.clicked.connect(self._generate_password_simple)

        btn_backup = QPushButton("Backup → Supabase")
        btn_backup.clicked.connect(self._on_backup)

        btn_restore = QPushButton("Restore ← Supabase")
        btn_restore.clicked.connect(self._on_restore)

        btn_sync = QPushButton("Sync")
        btn_sync.clicked.connect(self._on_sync)

        btn_local_backup = QPushButton("Backup local cifrado")
        btn_local_backup.clicked.connect(self._on_local_backup)

        btn_restore_local = QPushButton("Restaurar backup local")
        btn_restore_local.clicked.connect(self._on_local_restore)

        self.btn_toggle_drawer = QPushButton("Generador premium »")
        self.btn_toggle_drawer.clicked.connect(self._toggle_drawer)

        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_generate_simple)
        btn_layout.addWidget(btn_backup)
        btn_layout.addWidget(btn_restore)
        btn_layout.addWidget(btn_sync)
        btn_layout.addWidget(btn_local_backup)
        btn_layout.addWidget(btn_restore_local)
        btn_layout.addWidget(self.btn_toggle_drawer)

        btn_layout.addWidget(QLabel("Tema:"))
        self.theme_switch = ToggleSwitch()
        self.theme_switch.toggled.connect(self._toggle_theme)
        btn_layout.addWidget(self.theme_switch)

        left_layout.addLayout(btn_layout)

        # ---- Búsqueda ----
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Buscar:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filtrar por servicio o usuario...")
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input)
        left_layout.addLayout(search_layout)

        # ---- Tabla ----
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "", "Servicio", "Usuario", "Contraseña", "Copiar", "Ver", "Editar"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)
        left_layout.addWidget(self.table)

        # ========= STATUS BAR =========
        status_bar = QHBoxLayout()
        status_bar.setContentsMargins(12, 6, 12, 6)
        status_bar.setSpacing(25)

        self.logo_label = QLabel("🔐 PassGuardian")
        self.logo_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2d7dca;")
        status_bar.addWidget(self.logo_label)

        self.status_supabase = QLabel("Supabase: 🔴 Offline")
        self.status_supabase.setStyleSheet("font-size: 12px; font-weight: bold;")
        status_bar.addWidget(self.status_supabase)

        self.status_sqlite = QLabel("SQLite: 🟢 Online")
        self.status_sqlite.setStyleSheet("font-size: 12px; font-weight: bold;")
        status_bar.addWidget(self.status_sqlite)

        self.status_internet = QLabel("🌐❌ Sin conexión")
        self.status_internet.setStyleSheet("font-size: 12px; font-weight: bold;")
        status_bar.addWidget(self.status_internet)

        self.status_sync = QLabel("⬆️⬇️ Sin sincronizar")
        self.status_sync.setStyleSheet("font-size: 12px; font-weight: bold;")
        status_bar.addWidget(self.status_sync)

        self.status_datetime = QLabel("🕒 --:--")
        self.status_datetime.setStyleSheet("font-size: 12px; font-weight: bold;")
        status_bar.addWidget(self.status_datetime)

        status_bar.addStretch()
        left_layout.addLayout(status_bar)

        main_layout.addLayout(left_layout, stretch=3)

        # ========= DRAWER PREMIUM =========
        self.drawer = QWidget()
        self.drawer.setObjectName("drawer")
        self.drawer.setMaximumWidth(0)

        drawer_layout = QVBoxLayout(self.drawer)
        drawer_layout.setContentsMargins(18, 18, 18, 18)

        title = QLabel("Generador Premium 🔐")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        drawer_layout.addWidget(title)

        drawer_layout.addWidget(QLabel("Longitud de la contraseña"))
        self.length_label = QLabel("20 caracteres")
        drawer_layout.addWidget(self.length_label)

        self.length_slider = QSlider(Qt.Horizontal)
        self.length_slider.setMinimum(8)
        self.length_slider.setMaximum(32)
        self.length_slider.setValue(20)
        self.length_slider.valueChanged.connect(self._on_length_changed)
        drawer_layout.addWidget(self.length_slider)

        drawer_layout.addWidget(QLabel("Tipos de caracteres"))
        self.cb_upper = QCheckBox("Mayúsculas")
        self.cb_lower = QCheckBox("Minúsculas")
        self.cb_digits = QCheckBox("Números")
        self.cb_symbols = QCheckBox("Símbolos")
        for cb in [self.cb_upper, self.cb_lower, self.cb_digits, self.cb_symbols]:
            cb.setChecked(True)
            drawer_layout.addWidget(cb)

        drawer_layout.addWidget(QLabel("Modos avanzados"))
        self.rb_normal = QRadioButton("Normal")
        self.rb_max_entropy = QRadioButton("Máxima entropía")
        self.rb_strict = QRadioButton("Sitios estrictos")
        self.rb_safe = QRadioButton("Solo seguros")

        self.rb_normal.setChecked(True)

        self.modes_group = QButtonGroup(self)
        for rb in [self.rb_normal, self.rb_max_entropy, self.rb_strict, self.rb_safe]:
            self.modes_group.addButton(rb)
            drawer_layout.addWidget(rb)

        self.btn_generate = QPushButton("🔄 Generar contraseña")
        self.btn_generate.clicked.connect(self._generate_password_advanced)
        drawer_layout.addWidget(self.btn_generate)

        drawer_layout.addStretch()

        main_layout.addWidget(self.drawer, stretch=0)

        self.drawer_animation = QPropertyAnimation(self.drawer, b"maximumWidth")
        self.drawer_animation.setDuration(250)
        self.drawer_animation.setEasingCurve(QEasingCurve.InOutCubic)



    # ============================================================
    #   CRUD: AGREGAR SERVICIO
    # ============================================================
    def _on_add(self):
        dlg = ServiceDialog(self, "Agregar servicio")
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()

            self.sm.add_secret(
                data["service"],
                data["username"],
                data["secret"],
                data["notes"]
            )

            self._load_table()
            QMessageBox.information(self, "OK", "Servicio agregado correctamente.")

    # ============================================================
    #   CRUD: EDITAR SERVICIO
    # ============================================================
    def _on_edit(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Seleccione un registro para editar.")
            return

        service = self.table.item(row, 1).text()
        username = self.table.item(row, 2).text()

        records = self.sm.get_all()
        record = next(
            (r for r in records if r["service"] == service and r["username"] == username),
            None
        )

        if record is None:
            QMessageBox.critical(self, "Error", "No se encontró el registro en la base de datos.")
            return

        dlg = ServiceDialog(self, "Editar servicio", record)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()

            self.sm.update_secret(
                record["id"],
                data["service"],
                data["username"],
                data["secret"],
                data["notes"]
            )

            self._load_table()
            QMessageBox.information(self, "OK", "Servicio actualizado.")

    # ============================================================
    #   CRUD: ELIMINAR SERVICIO
    # ============================================================
    def _on_delete(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Seleccione un registro para eliminar.")
            return

        service = self.table.item(row, 1).text()
        username = self.table.item(row, 2).text()

        if QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Eliminar el servicio '{service}'?"
        ) != QMessageBox.Yes:
            return

        records = self.sm.get_all()
        record = next(
            (r for r in records if r["service"] == service and r["username"] == username),
            None
        )

        if record is None:
            QMessageBox.critical(self, "Error", "No se encontró el registro en la base de datos.")
            return

        self.sm.conn.execute("UPDATE secrets SET deleted = 1 WHERE id = ?", (record["id"],))
        self.sm.conn.commit()

        self._load_table()
        QMessageBox.information(self, "OK", "Servicio eliminado.")

    # ============================================================
    #   BACKUP LOCAL CIFRADO
    # ============================================================
    def _on_local_backup(self):
        try:
            path = self.sm.create_local_backup()
            QMessageBox.information(self, "Backup local", f"Backup local creado:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error en backup local", str(e))

    # ============================================================
    #   RESTORE LOCAL CIFRADO
    # ============================================================
    def _on_local_restore(self):
        try:
            self.sm.local_restore()
            self._load_table()
            QMessageBox.information(self, "Restore local", "Backup local restaurado correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error en restore local", str(e))

    # ============================================================
    #   MÉTODOS CORREGIDOS (INTERNET / SUPABASE)
    # ============================================================

    def _on_backup(self):
        try:
            self.sync_manager.backup_to_supabase()
            QMessageBox.information(self, "Backup", "Backup en Supabase completado.")
        except ConnectionError as e:
            QMessageBox.warning(self, "Sin conexión", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error en backup", str(e))

    def _on_restore(self):
        try:
            self.sync_manager.restore_from_supabase()
            self._load_table()
            QMessageBox.information(self, "Restore", "Restauración desde Supabase completada.")
        except ConnectionError as e:
            QMessageBox.warning(self, "Sin conexión", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error en restore", str(e))

    def _on_sync(self):
        try:
            self.sync_manager.sync()
            self._load_table()
            QMessageBox.information(self, "Sync", "Sincronización completada.")
        except ConnectionError as e:
            QMessageBox.warning(self, "Sin conexión", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error en sync", str(e))

    # ============================================================
    #   GENERADOR PREMIUM
    # ============================================================
    def _on_premium(self):
        self._toggle_drawer()

    def _on_length_changed(self, value):
        self.length_label.setText(f"{value} caracteres")

    # ============================================================
    #   BUSCADOR
    # ============================================================
    def _on_search_changed(self, text):
        text = text.lower().strip()
        for row in range(self.table.rowCount()):
            service = self.table.item(row, 1).text().lower()
            user = self.table.item(row, 2).text().lower()
            visible = text in service or text in user
            self.table.setRowHidden(row, not visible)

    # ============================================================
    #   CARGAR TABLA
    # ============================================================
    def _load_table(self):
        records = self.sm.get_all()
        self.table.setRowCount(0)

        for r in records:
            if r.get("deleted"):
                continue

            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 1, QTableWidgetItem(r["service"]))
            self.table.setItem(row, 2, QTableWidgetItem(r["username"]))

            hidden_pwd = "•" * 12
            self.table.setItem(row, 3, QTableWidgetItem(hidden_pwd))

            btn_copy = QPushButton("📋")
            btn_copy.clicked.connect(lambda _, pwd=r["secret"]: QApplication.clipboard().setText(pwd))
            self.table.setCellWidget(row, 4, btn_copy)

            btn_view = QPushButton("👁️")
            btn_view.clicked.connect(lambda _, row=row, pwd=r["secret"]: self._toggle_view_password(row, pwd))
            self.table.setCellWidget(row, 5, btn_view)

            btn_edit = QPushButton("✏️")
            btn_edit.clicked.connect(self._on_edit)
            self.table.setCellWidget(row, 6, btn_edit)

    def _toggle_view_password(self, row, pwd):
        current = self.table.item(row, 3).text()
        if "•" in current:
            self.table.setItem(row, 3, QTableWidgetItem(pwd))
        else:
            self.table.setItem(row, 3, QTableWidgetItem("•" * 12))

    # ============================================================
    #   DRAWER ANIMATION
    # ============================================================
    def _toggle_drawer(self):
        if self.drawer.maximumWidth() == 0:
            self.drawer_animation.setStartValue(0)
            self.drawer_animation.setEndValue(260)
        else:
            self.drawer_animation.setStartValue(self.drawer.maximumWidth())
            self.drawer_animation.setEndValue(0)
        self.drawer_animation.start()

    # ============================================================
    #   GENERADOR SIMPLE
    # ============================================================
    def _generate_password_simple(self):
        chars = string.ascii_letters + string.digits
        pwd = "".join(secrets.choice(chars) for _ in range(12))
        QMessageBox.information(self, "Contraseña generada", pwd)

    # ============================================================
    #   GENERADOR PREMIUM AVANZADO
    # ============================================================
    def _generate_password_advanced(self):
        length = self.length_slider.value()

        chars = ""
        if self.cb_upper.isChecked(): chars += string.ascii_uppercase
        if self.cb_lower.isChecked(): chars += string.ascii_lowercase
        if self.cb_digits.isChecked(): chars += string.digits
        if self.cb_symbols.isChecked(): chars += "!@#$%^&*()-_=+[]{}"

        if not chars:
            QMessageBox.warning(self, "Error", "Seleccione al menos un tipo de carácter.")
            return

        pwd = "".join(secrets.choice(chars) for _ in range(length))
        QMessageBox.information(self, "Contraseña generada", pwd)



    def _toggle_theme(self):
        # Método pendiente de implementar
        pass
