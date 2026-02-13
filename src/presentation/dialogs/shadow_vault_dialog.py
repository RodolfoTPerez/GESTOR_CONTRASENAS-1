from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QLabel, QHeaderView, QCheckBox,
    QWidget, QApplication, QFrame
)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QColor, QFont
from src.presentation.ui_utils import PremiumMessage
from src.presentation.theme_manager import ThemeManager
from src.domain.messages import MESSAGES

class ShadowVaultDialog(QDialog):
    """
    Bóveda de Sombras (Shadow Vault Explorer)
    Permite visualizar y recuperar registros marcados como eliminados.
    """
    def __init__(self, secrets_manager, sync_manager=None, parent=None):
        super().__init__(parent)
        self.sm = secrets_manager
        self.sync_manager = sync_manager
        self.selected_ids = set()
        
        self.theme = ThemeManager()
        self.settings = QSettings(ThemeManager.APP_ID, "VultraxCore_Global")
        
        active_theme = self.settings.value("theme_active", "tactical_dark")
        self.theme.set_theme(active_theme)
        
        # Fondo base instantáneo para evitar flasheo blanco
        colors = self.theme.get_theme_colors()
        self.setStyleSheet(f"QDialog {{ background-color: {colors['bg']}; }}")
        self.setStyleSheet(self.theme.load_stylesheet("dialogs"))
        
        self.setWindowTitle(MESSAGES.SHADOW.TITLE)
        self.resize(1100, 650)
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Header
        header_v = QVBoxLayout()
        title = QLabel(MESSAGES.SHADOW.HEADER)
        title.setObjectName("dialog_title")
        header_v.addWidget(title)
 
        subtitle = QLabel(MESSAGES.SHADOW.SUBTITLE)
        subtitle.setObjectName("dialog_subtitle")
        header_v.addWidget(subtitle)
        layout.addLayout(header_v)

        # Tabla Premium
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "", 
            MESSAGES.SHADOW.COL_SERVICE, 
            MESSAGES.SHADOW.COL_USER, 
            MESSAGES.SHADOW.COL_OWNER, 
            MESSAGES.SHADOW.COL_STATUS, 
            MESSAGES.SHADOW.COL_PRIVACY
        ])
        
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.Stretch)
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents) # Checkbox
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents) # Estado
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)

        layout.addWidget(self.table)

        # Footer Actions
        footer = QHBoxLayout()
        self.lbl_count = QLabel(f"0 {MESSAGES.SHADOW.LBL_SELECTED}")
        # [FIX] Use theme text_dim
        colors = self.theme.get_theme_colors()
        self.lbl_count.setStyleSheet(f"color: {colors['text_dim']}; font-weight: bold;")
        footer.addWidget(self.lbl_count)
        
        footer.addStretch()

        self.btn_resurrect = QPushButton(MESSAGES.SHADOW.BTN_RESURRECT)
        self.btn_resurrect.setObjectName("btn_primary")
        self.btn_resurrect.setEnabled(False)
        self.btn_resurrect.clicked.connect(self._on_resurrect)
        footer.addWidget(self.btn_resurrect)
 
        self.btn_purge = QPushButton(MESSAGES.SHADOW.BTN_PURGE)
        self.btn_purge.setObjectName("btn_danger")
        self.btn_purge.clicked.connect(self._on_purge)
        footer.addWidget(self.btn_purge)

        btn_close = QPushButton(MESSAGES.SHADOW.BTN_CLOSE)
        btn_close.setObjectName("btn_secondary")
        btn_close.clicked.connect(self.accept)
        footer.addWidget(btn_close)

        layout.addLayout(footer)

    def _load_data(self):
        self.table.setRowCount(0)
        self.selected_ids.clear()
        self.btn_resurrect.setEnabled(False)
        
        # Obtener todos incluyendo borrados
        records = self.sm.get_all(include_deleted=True)
        # Filtrar solo los borrados
        deleted_ones = [r for r in records if r.get("deleted") == 1]
        
        self.table.setRowCount(len(deleted_ones))
        
        for i, r in enumerate(deleted_ones):
            # Checkbox de selección
            ck = QCheckBox()
            ck.setStyleSheet("margin-left: 15px;")
            ck.stateChanged.connect(lambda state, rid=r["id"]: self._toggle_selection(rid, state))
            self.table.setCellWidget(i, 0, ck)
            
            # Datos básicos
            self.table.setItem(i, 1, QTableWidgetItem(str(r["service"])))
            self.table.setItem(i, 2, QTableWidgetItem(str(r["username"])))
            self.table.setItem(i, 3, QTableWidgetItem(str(r.get("owner_name", "---"))))
            
            # Estado de Llave (Garantía Criptográfica)
            is_blocked = (r.get("secret") == "[Bloqueado 🔑]")
            status_item = QTableWidgetItem(MESSAGES.SHADOW.STATUS_BLOCKED if is_blocked else MESSAGES.SHADOW.STATUS_READY)
            
            # [FIX] Use Theme Colors
            colors = self.theme.get_theme_colors()
            status_item.setForeground(QColor(colors["danger"]) if is_blocked else QColor(colors["success"]))
            
            status_item.setFont(QFont("Consolas", 9, QFont.Bold))
            status_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 4, status_item)
            
            # Privacidad
            priv_text = MESSAGES.SHADOW.PRIV_PRIVATE if r.get("is_private") == 1 else MESSAGES.SHADOW.PRIV_SHARED
            priv_item = QTableWidgetItem(priv_text)
            
            # [FIX] Use Theme Colors
            priv_item.setForeground(QColor(colors["warning"]) if r.get("is_private") == 1 else QColor(colors["primary"]))
            
            priv_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 5, priv_item)

    def _toggle_selection(self, rid, state):
        if state == Qt.Checked:
            self.selected_ids.add(rid)
        else:
            self.selected_ids.discard(rid)
        
        
        count = len(self.selected_ids)
        self.lbl_count.setText(f"{count} {MESSAGES.SHADOW.LBL_SELECTED}")
        self.btn_resurrect.setEnabled(count > 0)

    def _on_resurrect(self):
        count = len(self.selected_ids)
        if PremiumMessage.question(self, MESSAGES.SHADOW.MSG_RESURRECT_TITLE, MESSAGES.SHADOW.MSG_RESURRECT_CONFIRM.format(count=count)):
            try:
                for rid in self.selected_ids:
                    # Restauramos localmente
                    self.sm.restore_secret(rid)
                    # Forzamos sincronización inmediata si hay red
                    if self.sync_manager and self.sync_manager.check_internet():
                        self.sync_manager.sync_single_record(rid)
                
                PremiumMessage.success(self, MESSAGES.COMMON.TITLE_SUCCESS, MESSAGES.SHADOW.MSG_RESURRECT_SUCCESS.format(count=count))
                self._load_data() # Recargar tabla
            except Exception as e:
                PremiumMessage.error(self, MESSAGES.SHADOW.MSG_RESURRECT_ERROR, str(e))

    def _on_purge(self):
        if not self.selected_ids:
            PremiumMessage.info(self, MESSAGES.SHADOW.BTN_PURGE, MESSAGES.SHADOW.MSG_PURGE_INFO)
            return

        if PremiumMessage.question(self, MESSAGES.SHADOW.MSG_PURGE_WARN_TITLE, MESSAGES.SHADOW.MSG_PURGE_WARN_TEXT):
            try:
                for rid in self.selected_ids:
                    # [ESTRICTO] Borramos de la nube primero si hay red
                    if self.sync_manager and self.sync_manager.check_internet():
                        self.sync_manager.delete_from_supabase(rid)
                    # Borramos de la base de datos local (Hard Delete)
                    self.sm.hard_delete_secret(rid)
                
                # Compactar base de datos
                self.sm.conn.execute("VACUUM")
                
                PremiumMessage.success(self, MESSAGES.SHADOW.MSG_PURGE_WARN_TITLE, MESSAGES.SHADOW.MSG_PURGE_SUCCESS.format(count=len(self.selected_ids)))
                self._load_data()
            except Exception as e:
                PremiumMessage.error(self, MESSAGES.SHADOW.MSG_PURGE_ERROR, str(e))
