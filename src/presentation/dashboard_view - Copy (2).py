print(">>> DASHBOARD_VIEW CARGADO DESDE:", __file__)

import secrets
import string
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QLabel,
    QMessageBox, QProgressBar, QToolButton, QSlider,
    QCheckBox, QRadioButton, QButtonGroup, QApplication
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
        from PyQt5.QtGui import QPainter, QColor

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        radius = 20
        margin = 2

        if self.isChecked():
            x = self.width() - radius - margin
            color = QColor("#ffffff")
        else:
            x = margin
            color = QColor("#dddddd")

        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(x, margin, radius, radius)


# ============================================================
#   DASHBOARD PRINCIPAL
# ============================================================
class DashboardView(QWidget):
    def __init__(self, secrets_manager, sync_manager):
        super().__init__()
        self.sm = secrets_manager
        self.sync_mgr = sync_manager

        self.dark_mode = False
        self.drawer_open = False
        self.drawer_width_expanded = 320
        self._secrets_cache = []

        self.setWindowTitle("PassGuardian")
        self.resize(1100, 600)

        try:
            self._build_ui()
            self._load_table()

        except Exception as e:
            print("ERROR en inicialización:", repr(e))
            QMessageBox.critical(self, "Error crítico", str(e))

        # AUTO-LOCK
        self.inactivity_timer = QTimer()
        self.inactivity_timer.setInterval(INACTIVITY_LIMIT_MS)
        self.inactivity_timer.timeout.connect(self.lock_app)
        self.inactivity_timer.start()
        self.installEventFilter(self)
        # Reloj en tiempo real
        # Reloj en tiempo real
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_datetime)
        self.clock_timer.start(1000)

        # Verificar internet cada 5 segundos
        self.internet_timer = QTimer()
        self.internet_timer.timeout.connect(self._update_internet_realtime)
        self.internet_timer.start(5000)

        # Verificar Supabase cada 5 segundos
        self.supabase_timer = QTimer()
        self.supabase_timer.timeout.connect(self._update_supabase_realtime)
        self.supabase_timer.start(5000)

        # Verificar SQLite cada 10 segundos
        self.sqlite_timer = QTimer()
        self.sqlite_timer.timeout.connect(self._update_sqlite_realtime)
        self.sqlite_timer.start(10000)


        # Cargar estilo inicial
        try:
            qss_path = Path(__file__).resolve().parent / "style.qss"
            if qss_path.exists():
                with open(qss_path, "r") as f:
                    self.setStyleSheet(f.read())
        except Exception as e:
            print("Error cargando estilo inicial:", repr(e))

    # ============================================================
    #   EVENTOS DE ACTIVIDAD
    # ============================================================
    def eventFilter(self, obj, event):
        if event.type() in (
            QEvent.MouseMove,
            QEvent.MouseButtonPress,
            QEvent.KeyPress,
            QEvent.Wheel
        ):
            self.inactivity_timer.start()
        return super().eventFilter(obj, event)

    def lock_app(self):
        try:
            print(">>> Auto-lock activado")
            self.inactivity_timer.stop()
            self.hide()

            from src.presentation.login_view import LoginView

            def on_login_success(master_password, totp_secret):
                pass

            self.login_view = LoginView(on_login_success)
            self.login_view.show()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # ============================================================
    #   UI PRINCIPAL
    # ============================================================
    def _build_ui(self):
        main_layout = QHBoxLayout(self)

        # ========= LADO IZQUIERDO =========
        left_layout = QVBoxLayout()

        # ---- Formulario ----
        form_layout = QHBoxLayout()

        self.service_input = QLineEdit()
        self.user_input = QLineEdit()

        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)

        self.toggle_pass_btn = QToolButton()
        self.toggle_pass_btn.setText("👁️")
        self.toggle_pass_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_pass_btn.setStyleSheet("border: none; padding: 0px;")
        self.toggle_pass_btn.clicked.connect(self._toggle_password_visibility)

        pass_layout = QHBoxLayout()
        pass_layout.setContentsMargins(0, 0, 0, 0)
        pass_layout.addWidget(self.pass_input)
        pass_layout.addWidget(self.toggle_pass_btn)

        form_layout.addWidget(QLabel("Servicio:"))
        form_layout.addWidget(self.service_input)
        form_layout.addWidget(QLabel("Usuario:"))
        form_layout.addWidget(self.user_input)
        form_layout.addWidget(QLabel("Contraseña:"))
        form_layout.addLayout(pass_layout)

        # Barra de calidad
        self.strength_bar = QProgressBar()
        self.strength_bar.setRange(0, 100)
        self.strength_bar.setTextVisible(False)
        self.strength_bar.setFixedHeight(10)

        self.strength_label = QLabel("")

        form_layout.addWidget(self.strength_bar)
        form_layout.addWidget(self.strength_label)

        self.pass_input.textChanged.connect(self._update_strength_bar)

        left_layout.addLayout(form_layout)

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

        self.btn_toggle_drawer = QPushButton("Generador premium »")
        self.btn_toggle_drawer.clicked.connect(self._toggle_drawer)

        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_generate_simple)
        btn_layout.addWidget(btn_backup)
        btn_layout.addWidget(btn_restore)
        btn_layout.addWidget(btn_sync)
        btn_layout.addWidget(btn_local_backup)
        btn_layout.addWidget(self.btn_toggle_drawer)

        # Switch tema
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
        # ---- Tabla ----
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "", "Servicio", "Usuario", "Contraseña", "Copiar", "Ver"
        ])
        self.table.setAlternatingRowColors(True)

        # IMPORTANTE: desactivar ordenamiento mientras llenamos
        self.table.setSortingEnabled(False)

        left_layout.addWidget(self.table)
                # ========= STATUS BAR =========
        status_bar = QHBoxLayout()
        status_bar.setContentsMargins(12, 6, 12, 6)
        status_bar.setSpacing(25)

        # Logo + nombre
        self.logo_label = QLabel("🔐 PassGuardian")
        self.logo_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2d7dca;")
        status_bar.addWidget(self.logo_label)

        # Supabase
        self.status_supabase = QLabel("Supabase: 🔴 Offline")
        self.status_supabase.setStyleSheet("font-size: 12px; font-weight: bold;")
        status_bar.addWidget(self.status_supabase)

        # SQLite
        self.status_sqlite = QLabel("SQLite: 🟢 Online")
        self.status_sqlite.setStyleSheet("font-size: 12px; font-weight: bold;")
        status_bar.addWidget(self.status_sqlite)

        # Internet
        self.status_internet = QLabel("🌐 Sin conexión")
        self.status_internet.setStyleSheet("font-size: 12px; font-weight: bold;")
        status_bar.addWidget(self.status_internet)

        # Sincronización
        self.status_sync = QLabel("⬆️⬇️ Sin sincronizar")
        self.status_sync.setStyleSheet("font-size: 12px; font-weight: bold;")
        status_bar.addWidget(self.status_sync)

        # Fecha y hora
        self.status_datetime = QLabel("🕒 --:--")
        self.status_datetime.setStyleSheet("font-size: 12px; font-weight: bold;")
        status_bar.addWidget(self.status_datetime)

        status_bar.addStretch()
        left_layout.addLayout(status_bar)


        main_layout.addLayout(left_layout, stretch=3)

        # ========= DRAWER =========
        self.drawer = QWidget()
        self.drawer.setObjectName("drawer")
        self.drawer.setMaximumWidth(0)

        drawer_layout = QVBoxLayout(self.drawer)
        drawer_layout.setContentsMargins(18, 18, 18, 18)

        title = QLabel("Generador Premium 🔐")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        drawer_layout.addWidget(title)

        # Longitud
        drawer_layout.addWidget(QLabel("Longitud de la contraseña"))
        self.length_label = QLabel("20 caracteres")
        drawer_layout.addWidget(self.length_label)

        self.length_slider = QSlider(Qt.Horizontal)
        self.length_slider.setMinimum(8)
        self.length_slider.setMaximum(32)
        self.length_slider.setValue(20)
        self.length_slider.valueChanged.connect(self._on_length_changed)
        drawer_layout.addWidget(self.length_slider)

        # Tipos
        drawer_layout.addWidget(QLabel("Tipos de caracteres"))
        self.cb_upper = QCheckBox("Mayúsculas")
        self.cb_lower = QCheckBox("Minúsculas")
        self.cb_digits = QCheckBox("Números")
        self.cb_symbols = QCheckBox("Símbolos")
        for cb in [self.cb_upper, self.cb_lower, self.cb_digits, self.cb_symbols]:
            cb.setChecked(True)
            drawer_layout.addWidget(cb)

        # Modos
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

        # Botón generar
        self.btn_generate = QPushButton("🔄 Generar contraseña")
        self.btn_generate.clicked.connect(self._generate_password_advanced)
        drawer_layout.addWidget(self.btn_generate)

        drawer_layout.addStretch()

        main_layout.addWidget(self.drawer, stretch=0)

        # Animación drawer
        self.drawer_animation = QPropertyAnimation(self.drawer, b"maximumWidth")
        self.drawer_animation.setDuration(250)
        self.drawer_animation.setEasingCurve(QEasingCurve.InOutCubic)
        
        
        
        
    # ============================================================
    #   STATUS BAR UPDATES
    # ============================================================
    def update_supabase_status(self, connected: bool, syncing: bool = False):
        if syncing:
            self.status_supabase.setText("☁️📡 Transmitiendo datos a Supabase")
        elif connected:
            self.status_supabase.setText("Supabase: 🟢 Online")
        else:
            self.status_supabase.setText("Supabase: 🔴 Offline")

    def update_sqlite_status(self, online: bool):
        self.status_sqlite.setText("SQLite: 🟢 Online" if online else "SQLite: 🔴 Offline")

    def update_internet_status(self, connected: bool):
        self.status_internet.setText("🌐 Conectado" if connected else "🌐 Sin conexión")

    def update_sync_status(self, syncing: bool):
        self.status_sync.setText("⬆️⬇️ Sincronizando..." if syncing else "⬆️⬇️ Sincronización completa")

    def update_datetime(self):
        from datetime import datetime
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.status_datetime.setText(f"🕒 {now}")
        

    # ============================================================
    #   REAL CHECKS (INTERNET, SUPABASE, SQLITE)
    # ============================================================
    def check_internet(self) -> bool:
        import socket
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except OSError:
            return False

    def check_supabase(self) -> bool:
        import requests
        try:
            url = self.sync_mgr.supabase_url + "/rest/v1/"
            r = requests.get(url, timeout=3)
            return r.status_code in (200, 400, 401)
        except:
            return False

    def check_sqlite(self) -> bool:
        try:
            self.sm.get_all()
            return True
        except:
            return False
            
    # ============================================================
    #   REALTIME STATUS UPDATES
    # ============================================================
    def _update_internet_realtime(self):
        online = self.check_internet()
        self.update_internet_status(online)

    def _update_supabase_realtime(self):
        connected = self.check_supabase()
        self.update_supabase_status(connected)

    def _update_sqlite_realtime(self):
        online = self.check_sqlite()
        self.update_sqlite_status(online)

        

    # ============================================================
    #   MOSTRAR / OCULTAR CONTRASEÑA (FORMULARIO)
    # ============================================================
    def _toggle_password_visibility(self):
        if self.pass_input.echoMode() == QLineEdit.Password:
            self.pass_input.setEchoMode(QLineEdit.Normal)
            self.toggle_pass_btn.setText("🙈")
        else:
            self.pass_input.setEchoMode(QLineEdit.Password)
            self.toggle_pass_btn.setText("👁️")

    # ============================================================
    #   BARRA DE CALIDAD DE CONTRASEÑA
    # ============================================================
    def _update_strength_bar(self, text):
        score = 0

        if len(text) >= 8:
            score += 25
        if any(c.islower() for c in text) and any(c.isupper() for c in text):
            score += 25
        if any(c.isdigit() for c in text):
            score += 25
        if any(c in "!@#$%^&*()-_=+[]{}|;:'\",.<>?/`~" for c in text):
            score += 25

        self.strength_bar.setValue(score)

        if score >= 75:
            color = "#4CAF50"
            label = "Fuerte 🟢"
        elif score >= 50:
            color = "#FFC107"
            label = "Media 🟡"
        else:
            color = "#F44336"
            label = "Débil 🔴"

        self.strength_label.setText(f"Calidad: {label}")

        self.strength_bar.setStyleSheet(f"""
        QProgressBar {{
            border: 1px solid #ccc;
            border-radius: 5px;
            background-color: #eee;
        }}
        QProgressBar::chunk {{
            background-color: {color};
            border-radius: 5px;
        }}
        """)

    # ============================================================
    #   CARGAR TABLA
    # ============================================================
    # ============================================================
    #   CARGAR TABLA
    # ============================================================
    def _load_table(self):
        try:
            secrets_list = self.sm.get_all()

            print("=== DEBUG: REGISTROS OBTENIDOS ===")
            for s in secrets_list:
                print("TIPO:", type(s), "->", s)
            print("=== FIN DEBUG ===")

            # Cache para filtros
            self._secrets_cache = secrets_list[:]

            # Cargar SIEMPRE todo al inicio (sin filtro)
            self._apply_table_filter("")
        except Exception as e:
            print("ERROR al cargar la tabla:", repr(e))
            QMessageBox.critical(self, "Error", str(e))




    # ============================================================
    #   FILTRO DE TABLA (BÚSQUEDA)
    # ============================================================
    # ============================================================
    #   FILTRO DE TABLA (BÚSQUEDA)
    # ============================================================
    def _apply_table_filter(self, query: str):
        from PyQt5.QtGui import QColor

        query = (query or "").lower()

        # Desactivar ordenamiento mientras modificamos la tabla
        sorting_prev = self.table.isSortingEnabled()
        self.table.setSortingEnabled(False)

        # LIMPIAR TABLA COMPLETAMENTE
        self.table.clearContents()
        self.table.setRowCount(0)

        filtered = []
        for s in self._secrets_cache:
            # ignorar registros totalmente vacíos
            if (not s.get("service")
                    and not s.get("username")
                    and not s.get("secret")):
                continue

            service = (s.get("service") or "").strip()
            user = (s.get("username") or "").strip()
            pwd = (s.get("secret") or "").strip()

            if query:
                if query not in service.lower() and query not in user.lower():
                    continue

            filtered.append(s)

        print(f"DEBUG: total en cache={len(self._secrets_cache)}, filtrados={len(filtered)}")

        self.table.setRowCount(len(filtered))

        for row_idx, s in enumerate(filtered):
            service = s.get("service", "")
            user = s.get("username", "")
            pwd = s.get("secret", "")

            print(f"FILA {row_idx}: service={service!r}, user={user!r}, pwd_len={len(pwd)}")

            # Seguridad
            score = 0
            if len(pwd) >= 8:
                score += 25
            if any(c.islower() for c in pwd) and any(c.isupper() for c in pwd):
                score += 25
            if any(c.isdigit() for c in pwd):
                score += 25
            if any(c in "!@#$%^&*()-_=+[]{}|;:'\",.<>?/`~" for c in pwd):
                score += 25

            emoji = "🔒" if score >= 75 else "🔓"
            emoji_item = QTableWidgetItem(emoji)
            emoji_item.setTextAlignment(Qt.AlignCenter)
            emoji_item.setForeground(QColor("black"))
            self.table.setItem(row_idx, 0, emoji_item)

            service_item = QTableWidgetItem(service)
            service_item.setForeground(QColor("black"))
            self.table.setItem(row_idx, 1, service_item)

            user_item = QTableWidgetItem(user)
            user_item.setForeground(QColor("black"))
            self.table.setItem(row_idx, 2, user_item)

            masked = "•" * len(pwd) if pwd else ""
            pwd_item = QTableWidgetItem(masked)
            pwd_item.setForeground(QColor("black"))
            self.table.setItem(row_idx, 3, pwd_item)

            # Botón copiar contraseña
            btn_copy = QPushButton("📋")
            btn_copy.setCursor(Qt.PointingHandCursor)
            btn_copy.setStyleSheet("border: none; font-size: 16px;")
            btn_copy.clicked.connect(lambda _, p=pwd: self._copy_password(p))
            self.table.setCellWidget(row_idx, 4, btn_copy)

            # Botón mostrar/ocultar contraseña
            btn_show = QPushButton("👁️")
            btn_show.setCursor(Qt.PointingHandCursor)
            btn_show.setStyleSheet("border: none; font-size: 16px;")
            btn_show.clicked.connect(
                lambda _, r=row_idx, pw=pwd: self._toggle_row_password(r, pw)
            )
            self.table.setCellWidget(row_idx, 5, btn_show)

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

        # Restaurar estado de ordenamiento si estaba activo
        self.table.setSortingEnabled(sorting_prev)

    # ============================================================
    #   COPIAR CONTRASEÑA
    # ============================================================
    def _copy_password(self, pwd):
        clipboard = QApplication.clipboard()
        clipboard.setText(pwd)
        QMessageBox.information(self, "Copiado", "Contraseña copiada al portapapeles.")

    # ============================================================
    #   MOSTRAR / OCULTAR CONTRASEÑA POR FILA
    # ============================================================
    def _toggle_row_password(self, row, pwd):
        item = self.table.item(row, 3)
        if item is None:
            return

        if item.text().startswith("•"):
            item.setText(pwd)
        else:
            item.setText("•" * len(pwd))

    # ============================================================
    #   BÚSQUEDA EN TIEMPO REAL
    # ============================================================
    def _on_search_changed(self, text):
        try:
            self._apply_table_filter(text)
        except Exception as e:
            print("ERROR en búsqueda:", repr(e))

    # ============================================================
    #   AGREGAR SECRETO
    # ============================================================
    def _on_add(self):
        print(">>> _on_add EXISTE Y SE ESTÁ CARGANDO")

        service = self.service_input.text().strip()
        user = self.user_input.text().strip()
        pwd = self.pass_input.text().strip()
    

        if not service or not user or not pwd:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios.")
            return

        try:
            self.sm.add_secret(service, user, pwd)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        self.service_input.clear()
        self.user_input.clear()
        self.pass_input.clear()
        self.strength_bar.setValue(0)
        self.strength_label.setText("")

        self._load_table()



    # ============================================================
    #   BACKUP / RESTORE / SYNC / LOCAL BACKUP
    # ============================================================
    def _on_backup(self):
        try:
            self.update_supabase_status(True, syncing=True)
            self.update_sync_status(True)

            self.sync_mgr.backup_to_supabase()

            self.update_supabase_status(True)
            self.update_sync_status(False)

            QMessageBox.information(self, "Backup", "Backup completado.")
        except Exception as e:
            self.update_supabase_status(False)
            self.update_sync_status(False)
            QMessageBox.critical(self, "Error", str(e))


    def _on_restore(self):
        try:
            self.update_supabase_status(True, syncing=True)
            self.update_sync_status(True)

            self.sync_mgr.restore_from_supabase()
            self._load_table()

            self.update_supabase_status(True)
            self.update_sync_status(False)

            QMessageBox.information(self, "Restore", "Restauración completada.")
        except Exception as e:
            self.update_supabase_status(False)
            self.update_sync_status(False)
            QMessageBox.critical(self, "Error", str(e))


    def _on_sync(self):
        try:
            self.update_supabase_status(True, syncing=True)
            self.update_sync_status(True)

            self.sync_mgr.sync()
            self._load_table()

            self.update_supabase_status(True)
            self.update_sync_status(False)

            QMessageBox.information(self, "Sync", "Sincronización completada.")
        except Exception as e:
            self.update_supabase_status(False)
            self.update_sync_status(False)
            QMessageBox.critical(self, "Error", str(e))


    def _on_local_backup(self):
        try:
            backup_path = self.sm.create_local_backup()
            QMessageBox.information(self, "Backup local", f"Backup creado:\n{backup_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # ============================================================
    #   DRAWER
    # ============================================================
    def _toggle_drawer(self):
        if self.drawer_open:
            self.drawer_animation.stop()
            self.drawer_animation.setStartValue(self.drawer.maximumWidth())
            self.drawer_animation.setEndValue(0)
            self.drawer_animation.start()
            self.drawer_open = False
            self.btn_toggle_drawer.setText("Generador premium »")
        else:
            self.drawer_animation.stop()
            self.drawer_animation.setStartValue(self.drawer.maximumWidth())
            self.drawer_animation.setEndValue(self.drawer_width_expanded)
            self.drawer_animation.start()
            self.drawer_open = True
            self.btn_toggle_drawer.setText("Generador premium «")

    # ============================================================
    #   SLIDER LONGITUD
    # ============================================================
    def _on_length_changed(self, value):
        self.length_label.setText(f"{value} caracteres")

    # ============================================================
    #   GENERADOR RÁPIDO
    # ============================================================
    def _generate_password_simple(self):
        length = 16
        alphabet = (
            string.ascii_lowercase +
            string.ascii_uppercase +
            string.digits +
            "!@#$%^&*()-_=+[]{}|;:'\",.<>?/`~"
        )

        pwd = ''.join(secrets.choice(alphabet) for _ in range(length))

        self.pass_input.setText(pwd)
        self._update_strength_bar(pwd)

        if self.pass_input.echoMode() == QLineEdit.Normal:
            self.toggle_pass_btn.setText("🙈")
        else:
            self.toggle_pass_btn.setText("👁️")

    # ============================================================
    #   GENERADOR AVANZADO (DRAWER)
    # ============================================================
    def _generate_password_advanced(self):
        length = self.length_slider.value()

        upper = self.cb_upper.isChecked()
        lower = self.cb_lower.isChecked()
        digits = self.cb_digits.isChecked()
        symbols = self.cb_symbols.isChecked()

        # Modos especiales
        if self.rb_max_entropy.isChecked():
            upper = lower = digits = symbols = True
            if length < 20:
                length = 20
                self.length_slider.setValue(20)

        elif self.rb_strict.isChecked():
            upper = lower = digits = True
            symbols = False

        elif self.rb_safe.isChecked():
            upper = lower = digits = True
            symbols = False

        alphabet = ""

        if self.rb_safe.isChecked():
            safe_lower = "abcdefghijkmnopqrstuvwxyz"
            safe_upper = "ABCDEFGHJKLMNPQRSTUVWXYZ"
            safe_digits = "23456789"
            if lower:
                alphabet += safe_lower
            if upper:
                alphabet += safe_upper
            if digits:
                alphabet += safe_digits
        else:
            if lower:
                alphabet += string.ascii_lowercase
            if upper:
                alphabet += string.ascii_uppercase
            if digits:
                alphabet += string.digits
            if symbols:
                alphabet += "!@#$%^&*()-_=+[]{}|;:'\",.<>?/`~"

        if not alphabet:
            QMessageBox.warning(
                self,
                "Generador",
                "Debes seleccionar al menos un tipo de carácter."
            )
            return

        pwd = ''.join(secrets.choice(alphabet) for _ in range(length))

        self.pass_input.setText(pwd)
        self._update_strength_bar(pwd)

        if self.pass_input.echoMode() == QLineEdit.Normal:
            self.toggle_pass_btn.setText("🙈")
        else:
            self.toggle_pass_btn.setText("👁️")

    # ============================================================
    #   CAMBIO DE TEMA (LIGHT / DARK)
    # ============================================================
    def _toggle_theme(self, checked):
        self.dark_mode = bool(checked)
        base_path = Path(__file__).resolve().parent

        if self.dark_mode:
            file = base_path / "style_dark.qss"
        else:
            file = base_path / "style.qss"

        try:
            with open(file, "r") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print("ERROR cargando tema:", e)
