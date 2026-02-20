from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QFrame, QLineEdit, QHBoxLayout
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QColor
from src.presentation.ui_utils import PremiumMessage
from src.presentation.theme_manager import ThemeManager

class MaintenanceDialog(QDialog):
    def __init__(self, secrets_manager, parent=None):
        super().__init__(parent)
        self.sm = secrets_manager
        self._init_ui()
        
    def _init_ui(self):
        self.setWindowTitle("SISTEMA DE MANTENIMIENTO TÁCTICO")
        self.setFixedSize(500, 450)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        tm = ThemeManager()
        self.setStyleSheet(tm.apply_tokens("""
            QDialog {
                background-color: @bg_sec;
                border: 2px solid @primary;
                border-radius: @border-radius-main;
            }
            #MainFrame {
                background-color: @bg_sec;
                border: 2px solid @primary;
                border-radius: @border-radius-main;
            }
            QLabel { color: @accent; font-family: 'Consolas'; }
            #Title { font-size: 18px; font-weight: bold; color: @primary; }
            #Warning { color: #ff5000; font-size: 11px; font-weight: bold; }
            
            QPushButton {
                background-color: @bg;
                border: 1px solid @ghost_primary_30;
                color: @accent;
                padding: 10px;
                font-family: 'Consolas';
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                border: 1px solid @primary;
                background-color: @ghost_primary_15;
            }
            #NukeButton { border-color: #ff5000; color: #ff5000; }
            #NukeButton:hover { background-color: rgba(255, 80, 0, 0.1); }
            
            QLineEdit {
                background-color: @bg;
                border: 1px solid @ghost_primary_30;
                color: @accent;
                padding: 8px;
                border-radius: 4px;
            }
        """))
        
        layout = QVBoxLayout(self)
        self.frame = QFrame()
        self.frame.setObjectName("MainFrame")
        frame_layout = QVBoxLayout(self.frame)
        
        # Header
        title = QLabel("☢️ EMERGENCY MAINTENANCE ☢️")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(title)
        
        warn = QLabel("¡ATENCIÓN! Estas herramientas pueden alterar permanentemente el estado local.")
        warn.setObjectName("Warning")
        warn.setAlignment(Qt.AlignCenter)
        warn.setWordWrap(True)
        frame_layout.addWidget(warn)
        
        frame_layout.addSpacing(20)
        
        # Action 1: Nuclear Reset
        nuke_label = QLabel("1. RESETEO NUCLEAR (Limpieza Local)")
        nuke_label.setStyleSheet("font-weight: bold;")
        frame_layout.addWidget(nuke_label)
        
        nuke_desc = QLabel("Elimina la base de datos local para forzar una sincronización limpia desde la nube. No afecta los datos en Supabase.")
        nuke_desc.setStyleSheet("color: #64748b; font-size: 10px;")
        nuke_desc.setWordWrap(True)
        frame_layout.addWidget(nuke_desc)
        
        self.btn_nuke = QPushButton("EJECUTAR LIMPIEZA NUCLEAR")
        self.btn_nuke.setObjectName("NukeButton")
        self.btn_nuke.clicked.connect(self._exec_nuke)
        frame_layout.addWidget(self.btn_nuke)
        
        frame_layout.addSpacing(30)
        
        # Action 2: Repair Vault Key
        repair_label = QLabel("2. REPARACIÓN DE LLAVE (Regenerar VMK)")
        repair_label.setStyleSheet("font-weight: bold;")
        frame_layout.addWidget(repair_label)
        
        repair_desc = QLabel("Regenera la llave maestra de la bóveda usando tu password actual. Útil si recibes errores de 'Key Mismatch'.")
        repair_desc.setStyleSheet("color: #64748b; font-size: 10px;")
        repair_desc.setWordWrap(True)
        frame_layout.addWidget(repair_desc)
        
        self.pwd_input = QLineEdit()
        self.pwd_input.setPlaceholderText("Ingresa Master Password para validar...")
        self.pwd_input.setEchoMode(QLineEdit.Password)
        frame_layout.addWidget(self.pwd_input)
        
        self.btn_repair = QPushButton("REGENERAR LLAVE MAESTRA")
        self.btn_repair.clicked.connect(self._exec_repair)
        frame_layout.addWidget(self.btn_repair)
        
        frame_layout.addStretch()
        
        # Close Button
        self.btn_close = QPushButton("CERRAR TERMINAL DE MANTENIMIENTO")
        self.btn_close.clicked.connect(self.reject)
        self.btn_close.setStyleSheet("background-color: transparent; border: none; color: #475569; font-size: 10px;")
        frame_layout.addWidget(self.btn_close)
        
        layout.addWidget(self.frame)

    def _exec_nuke(self):
        if PremiumMessage.question(self, "CONFIRMACIÓN NUCLEAR", "¿Estás seguro de que deseas eliminar el estado local? Esto reiniciará la aplicación."):
            count = self.sm.nuclear_reset()
            PremiumMessage.success(self, "LIMPIEZA COMPLETADA", f"Se han eliminado {count} archivos. La aplicación se cerrará ahora.")
            import sys
            sys.exit(0)

    def _exec_repair(self):
        pwd = self.pwd_input.text()
        if not pwd:
            PremiumMessage.error(self, "DATOS FALTANTES", "Debes ingresar tu Master Password.")
            return
            
        username = self.sm.current_user if self.sm.current_user else "RODOLFO" # Fallback heuristic
        
        if PremiumMessage.question(self, "CONFIRMACIÓN DE REPARACIÓN", "Esto regenerará tu llave de acceso local. ¿Continuar?"):
            success = self.sm.repair_vault_key(username, pwd)
            if success:
                PremiumMessage.success(self, "LLAVE REGENERADA", "La reparación ha sido exitosa. Intenta loguearte normalmente.")
                self.accept()
            else:
                PremiumMessage.error(self, "FALLA EN REPARACIÓN", "No se pudo regenerar la llave. Verifica tu password.")
