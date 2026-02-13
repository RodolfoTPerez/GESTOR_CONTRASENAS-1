from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QLabel, QHeaderView, QFrame
)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QColor, QFont
from src.presentation.ui_utils import PremiumMessage
import logging

from src.presentation.theme_manager import ThemeManager

class AuditDialog(QDialog):
    def __init__(self, secrets_manager, sync_manager=None, user_role="user", parent=None):
        super().__init__(parent)
        self.sm = secrets_manager
        self.sync_manager = sync_manager
        self.user_role = user_role
        self.logger = logging.getLogger(__name__)
        self.view_mode = "local" # or "remote"
        from PyQt5.QtCore import QSettings
        self.settings = QSettings(ThemeManager.APP_ID, "VultraxCore_Global")
        self.theme = ThemeManager()
        active_theme = self.settings.value("theme_active", "tactical_dark")
        self.theme.set_theme(active_theme)
        
        # Fondo base instantáneo para evitar flasheo blanco
        colors = self.theme.get_theme_colors()
        self.setStyleSheet(f"QDialog {{ background-color: {colors['bg']}; }}")
        self.setStyleSheet(self.theme.load_stylesheet("dialogs"))
        
        self.setWindowTitle("📜 Auditoría de Seguridad - PassGuardian")
        self.resize(1100, 700)
        self._setup_ui()
        self._load_logs()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # Header con Estilo
        header_h = QHBoxLayout()
        header_v = QVBoxLayout()
        header = QLabel("Registro de Actividad y Seguridad")
        header.setObjectName("dialog_title")
        header_v.addWidget(header)
 
        self.sub = QLabel("Historial de todas las operaciones realizadas en la bóveda local.")
        self.sub.setObjectName("dialog_subtitle")
        header_v.addWidget(self.sub)
 
        # NUEVO: Indicador de Estado/Actualizando
        self.lbl_status = QLabel("") 
        self.lbl_status.setObjectName("status_indicator")
        header_v.addWidget(self.lbl_status)
        
        header_h.addLayout(header_v)
        header_h.addStretch()

        # Selector de Modo (Solo para Admin)
        if str(self.user_role).lower() == "admin":
            mode_frame = QFrame()
            mode_frame.setObjectName("container")
            mode_layout = QHBoxLayout(mode_frame)
            mode_layout.setContentsMargins(5, 5, 5, 5)

            self.btn_local = QPushButton("💻 LOCAL")
            self.btn_local.setCheckable(True)
            self.btn_local.setChecked(True)
            self.btn_local.clicked.connect(lambda: self._set_mode("local"))
            
            self.btn_remote = QPushButton("🌐 GLOBAL")
            self.btn_remote.setCheckable(True)
            self.btn_remote.clicked.connect(lambda: self._set_mode("remote"))
            
            mode_layout.addWidget(self.btn_local)
            mode_layout.addWidget(self.btn_remote)
            header_h.addWidget(mode_frame)

        layout.addLayout(header_h)

        # Tabla de Auditoría
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Fecha/Hora", "Usuario", "Acción", "Servicio", "Detalles", "Dispositivo", "Estado"
        ])
        
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.Stretch)
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(6, QHeaderView.ResizeToContents)

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.setStyleSheet(self.theme.load_stylesheet("dialogs"))
 
        if str(self.user_role).lower() == "admin":
            self.btn_local.setObjectName("btn_secondary")
            self.btn_remote.setObjectName("btn_secondary")
            self.btn_local.setFixedHeight(30)
            self.btn_remote.setFixedHeight(30)
        
        layout.addWidget(self.table)

        # Botones de Acción
        btn_layout = QHBoxLayout()
        
        self.btn_refresh = QPushButton("🔄 Actualizar")
        self.btn_refresh.setObjectName("btn_primary")
        self.btn_refresh.clicked.connect(self._load_logs)
        self.btn_refresh.setFixedWidth(120)
        
        self.btn_clear = QPushButton("🗑️ Limpiar Local")
        self.btn_clear.setObjectName("btn_danger")
        self.btn_clear.clicked.connect(self._on_clear_logs)
        self.btn_clear.setFixedWidth(150)

        self.btn_close = QPushButton("Cerrar")
        self.btn_close.setObjectName("btn_secondary")
        self.btn_close.clicked.connect(self.accept)
        self.btn_close.setFixedWidth(100)

        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        
        layout.addLayout(btn_layout)

    def _set_mode(self, mode):
        self.view_mode = mode
        self.btn_local.setChecked(mode == "local")
        self.btn_remote.setChecked(mode == "remote")
        self.sub.setText(f"Historial de todas las operaciones realizadas en la {'bóveda local' if mode == 'local' else 'NUBE (Global)'}.")
        self.btn_clear.setEnabled(mode == "local")
        self._load_logs()

    def _load_logs(self):
        self.lbl_status.setText("⏳ ACTUALIZANDO DATOS...")
        self.btn_refresh.setEnabled(False)
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents() # Forzar actualización visual

        try:
            self.table.setRowCount(0) # Limpiar antes de cargar
            logs = []
            
            if self.view_mode == "local":
                logs = self.sm.get_audit_logs(limit=500)
            else:
                # Cargar desde Supabase vía SyncManager
                import requests
                # [PRIVACY FIX] Solo cargar logs propios a menos que sea ADMIN en modo Global
                is_admin_global = (str(self.user_role).lower() == "admin" and self.view_mode == "remote")
                
                if is_admin_global:
                    url = f"{self.sync_manager.supabase_url}/rest/v1/security_audit?select=*&order=timestamp.desc&limit=200"
                else:
                    user_filter = f"user_name=ilike.{self.sync_manager.sm.current_user}"
                    url = f"{self.sync_manager.supabase_url}/rest/v1/security_audit?{user_filter}&select=*&order=timestamp.desc&limit=100"
                
                r = requests.get(url, headers=self.sync_manager.headers, timeout=5)
                if r.status_code == 200:
                    logs = r.json()
                else:
                    self.logger.error(f"Error fetching remote logs: {r.text}")
                    raise Exception(f"Error de red o permisos: {r.text}")

            if not logs:
                self.lbl_status.setText(f"📋 MODO: {self.view_mode.upper()} (Sin registros)")
                self.btn_refresh.setEnabled(True)
                return

            self.table.setRowCount(len(logs))
            for i, row in enumerate(logs):
                ts = row.get("timestamp", 0)
                uname = row.get("user_name", "SYSTEM")
                act = row.get("action", "-")
                svc = row.get("service", "")
                det = row.get("details", "")
                dev = row.get("device_info", "-")
                st = row.get("status", "-")

                dt = QDateTime.fromSecsSinceEpoch(int(ts)).toString("yyyy-MM-dd HH:mm:ss") if ts else "---"
                self.table.setItem(i, 0, QTableWidgetItem(dt))
                self.table.item(i, 0).setTextAlignment(Qt.AlignCenter)
                
                self.table.setItem(i, 1, QTableWidgetItem(str(uname)))
                self.table.item(i, 1).setTextAlignment(Qt.AlignCenter)
                
                item_act = QTableWidgetItem(str(act))
                item_act.setTextAlignment(Qt.AlignCenter)
                colors = self.theme.get_theme_colors()
                if any(x in str(act) for x in ["FISICA", "PURGA", "ELIMINAR"]):
                    item_act.setForeground(QColor(colors["danger"]))
                    item_act.setFont(QFont("Segoe UI", -1, QFont.Bold))
                self.table.setItem(i, 2, item_act)
                
                self.table.setItem(i, 3, QTableWidgetItem(str(svc)))
                self.table.item(i, 3).setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 4, QTableWidgetItem(str(det)))
                self.table.setItem(i, 5, QTableWidgetItem(str(dev)))
                self.table.item(i, 5).setTextAlignment(Qt.AlignCenter)
                
                item_st = QTableWidgetItem(str(st))
                item_st.setTextAlignment(Qt.AlignCenter)
                item_st.setForeground(QColor(colors["success"]) if st == "SUCCESS" else QColor(colors["danger"]))
                self.table.setItem(i, 6, item_st)

            self.lbl_status.setText(f"✅ VISTA: {self.view_mode.upper()}")

        except Exception as e:
            self.lbl_status.setText("❌ ERROR DE CARGA")
            PremiumMessage.error(self, "Error de Auditoría", f"Fallo al cargar registros: {e}")
        finally:
            self.btn_refresh.setEnabled(True)

    def _on_clear_logs(self):
        if PremiumMessage.question(self, "Confirmar Borrado", "¿Deseas borrar TODO el historial de auditoría LOCAL?"):
            try:
                self.sm.conn.execute("DELETE FROM security_audit")
                self.sm.conn.commit()
                self._load_logs()
                PremiumMessage.success(self, "Auditoría", "Historial local limpiado.")
            except Exception as e:
                PremiumMessage.error(self, "Error", str(e))
