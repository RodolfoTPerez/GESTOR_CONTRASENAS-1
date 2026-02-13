from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QHeaderView, QLabel, QFrame, QWidget, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QColor, QFont
from src.domain.messages import MESSAGES
from src.presentation.ui_utils import PremiumMessage
import time
import logging
from src.presentation.theme_manager import ThemeManager

class SessionsDialog(QDialog):
    def __init__(self, sync_manager, current_username=None, parent=None):
        super().__init__(parent)
        self.sync_manager = sync_manager
        self.logger = logging.getLogger(__name__)
        
        # [SENIOR FIX] Use Standardized User Scope
        from PyQt5.QtCore import QSettings
        if current_username:
            self.settings = QSettings(ThemeManager.APP_ID, f"VultraxCore_{current_username}")
        else:
            self.settings = QSettings(ThemeManager.APP_ID, "VultraxCore_Global")
            
        self.theme = ThemeManager()
        active_theme = self.settings.value("theme_active", "tactical_dark")
        self.theme.set_theme(active_theme)
        
        # [PROFESSIONAL UI] Frameless Window Strategy
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(850, 580)
        
        # Main Layout (Outer Wrapper for Shadow)
        self.outer_layout = QVBoxLayout(self)
        self.outer_layout.setContentsMargins(10, 10, 10, 10) # Space for shadow
        
        # Content Frame
        self.frame = QFrame()
        self.frame.setObjectName("DialogFrame")
        self.frame.setAttribute(Qt.WA_StyledBackground, True)
        
        # Drop Shadow for Depth (Realism)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 5)
        self.frame.setGraphicsEffect(shadow)
        
        self.outer_layout.addWidget(self.frame)

        # Apply theme specific to dialogs
        self.setStyleSheet(self.theme.load_stylesheet("dialogs"))
        
        # Internal Content Layout
        layout = QVBoxLayout(self.frame)
        layout.setContentsMargins(0, 0, 0, 0) # Zero margins because we have custom header
        layout.setSpacing(0)

        # --- CUSTOM TITLE BAR (Draggable) ---
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(50)
        self.title_bar.setObjectName("CustomTitleBar")
        
        # Ensure title bar matches theme bg via QSS (or fallback)
        colors = self.theme.get_theme_colors()
        self.title_bar.setStyleSheet(f"""
            QFrame#CustomTitleBar {{
                background-color: {colors.get('bg_sec', '#111')};
                border-bottom: 2px solid {colors.get('border', '#333')};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
        """)
        
        tb_layout = QHBoxLayout(self.title_bar)
        tb_layout.setContentsMargins(20, 0, 20, 0)
        
        tb_icon = QLabel("📡")
        tb_icon.setStyleSheet("font-size: 18px;")
        tb_title = QLabel(MESSAGES.SESSIONS.TITLE)
        tb_title.setStyleSheet(f"font-weight: 900; font-size: 14px; letter-spacing: 1px; color: {colors.get('text', '#fff')};")
        
        tb_layout.addWidget(tb_icon)
        tb_layout.addSpacing(10)
        tb_layout.addWidget(tb_title)
        tb_layout.addStretch()
        
        # Custom Close Button
        btn_win_close = QPushButton("×")
        btn_win_close.setFixedSize(30, 30)
        btn_win_close.setCursor(Qt.PointingHandCursor)
        btn_win_close.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {colors.get('text_dim', '#888')};
                font-size: 24px;
                border: none;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: {colors.get('danger', '#f00')};
            }}
        """)
        btn_win_close.clicked.connect(self.reject)
        tb_layout.addWidget(btn_win_close)
        
        layout.addWidget(self.title_bar)

        # --- CONTENT AREA ---
        content_widget = QWidget()
        content_l = QVBoxLayout(content_widget)
        content_l.setContentsMargins(35, 25, 35, 35) # Padding for internal content
        content_l.setSpacing(20)
        
        desc = QLabel(MESSAGES.SESSIONS.DESC)
        desc.setObjectName("dialog_subtitle")
        content_l.addWidget(desc)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            MESSAGES.SESSIONS.COL_USER, MESSAGES.SESSIONS.COL_DEVICE, MESSAGES.SESSIONS.COL_IP, 
            MESSAGES.SESSIONS.COL_ACTIVITY, MESSAGES.SESSIONS.COL_PRESENCE, MESSAGES.SESSIONS.COL_ACTION
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        content_l.addWidget(self.table)
        
        # Footer
        footer = QHBoxLayout()
        self.btn_refresh = QPushButton(MESSAGES.SESSIONS.BTN_REFRESH)
        self.btn_refresh.setObjectName("btn_primary")
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.load_sessions)
        footer.addWidget(self.btn_refresh)
        
        footer.addStretch()
        
        self.btn_close = QPushButton(MESSAGES.SESSIONS.BTN_CLOSE)
        self.btn_close.setObjectName("btn_secondary")
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.clicked.connect(self.accept)
        footer.addWidget(self.btn_close)
        
        content_l.addLayout(footer)
        layout.addWidget(content_widget)
        
        # [IP FIX] Send immediate heartbeat to ensure current session shows IP
        try:
            self.sync_manager.send_heartbeat("VIEW_SESSIONS", "ACTIVE")
        except:
            pass  # Silent fail if offline
        
        self.load_sessions()
        
        # Enable dragging
        self.old_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Only allow dragging from title bar area
            if self.title_bar.geometry().contains(self.frame.mapFromGlobal(event.globalPos())):
                self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPos() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def load_sessions(self):
        self.table.setRowCount(0)
        try:
            sessions = self.sync_manager.get_active_sessions()
            self.logger.info(f"Active sessions received: {len(sessions)}")
            if not sessions: return

            self.table.setRowCount(len(sessions))
            now = time.time()
            sessions.sort(key=lambda x: x.get("last_seen", 0), reverse=True)

            for row, s in enumerate(sessions):
                user_item = QTableWidgetItem(f"👤 {s.get('username', '???')}")
                user_item.setTextAlignment(Qt.AlignCenter)
                user_item.setFont(QFont("Segoe UI", -1, QFont.Bold))
                self.table.setItem(row, 0, user_item)

                device_item = QTableWidgetItem(f"💻 {s.get('device_name', 'Unknown')}")
                device_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 1, device_item)

                ip_item = QTableWidgetItem(s.get("ip_address", "---"))
                ip_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 2, ip_item)
                
                last_seen = s.get("last_seen", 0)
                diff = int(now - last_seen)
                
                is_revoked = s.get("is_revoked", False)
                colors = self.theme.get_theme_colors()
                
                # TRANSLATION LOGIC FOR TIME/STATUS
                # Assuming "HACE {}m" patterns need simple text replacement or format
                # For now using simple logic matching previous one but localized
                
                if is_revoked:
                    time_str = MESSAGES.SESSIONS.TIME_AGO_KICK
                    status = MESSAGES.SESSIONS.STATUS_KICK
                    color = colors["danger"]
                elif diff < 120:
                    time_str = MESSAGES.SESSIONS.TIME_NOW
                    status = MESSAGES.SESSIONS.STATUS_ONLINE
                    color = colors["success"]
                elif diff < 3600:
                    # Dynamic time string logic - hard to put in messages perfectly without format
                    # But we can assume M/H suffix is universal enough or just format it
                    # "HACE {m}m" / "AGO {m}m"
                    time_str = f"{int(diff // 60)}m" # Simple format: 5m. Or we can use a format string if needed.
                    # Previous was: f"HACE {diff // 60}m"
                    # Let's verify MESSAGES structure.
                    # I didn't add keys for "HACE {}m". I'll use a simple "5m ago" style or just keep number+suffix if acceptable.
                    # User wants "TODO EN INGLES". "HACE" is Spanish.
                    # I will use "AGO {x}m" pattern if EN, "HACE {x}m" if ES.
                    # Hack: Check MESSAGES.LANG. 
                    prefix = "AGO " if MESSAGES.LANG == "EN" else "HACE "
                    time_str = f"{prefix}{int(diff // 60)}m"
                    
                    status = MESSAGES.SESSIONS.STATUS_IDLE
                    color = colors["warning"]
                else:
                    prefix = "AGO " if MESSAGES.LANG == "EN" else "HACE "
                    time_str = f"{prefix}{int(diff // 3600)}h"
                    status = MESSAGES.SESSIONS.STATUS_DISCONNECTED
                    color = colors["danger"]
                    
                time_item = QTableWidgetItem(time_str)
                time_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 3, time_item)
                
                status_item = QTableWidgetItem(f"● {status}")
                status_item.setTextAlignment(Qt.AlignCenter)
                status_item.setForeground(QColor(color))
                status_item.setFont(QFont("Segoe UI", -1, QFont.Black))
                self.table.setItem(row, 4, status_item)
                
                import socket
                current_host = socket.gethostname()
                is_me = (s.get("username").upper() == self.sync_manager.sm.current_user.upper() and 
                         s.get("device_name") == current_host)
                
                if not is_me and s.get("username"):
                    btn_kill = QPushButton(MESSAGES.SESSIONS.BTN_KILL)
                    btn_kill.setObjectName("btn_danger")
                    btn_kill.setCursor(Qt.PointingHandCursor)
                    btn_kill.clicked.connect(lambda _, u=s.get("username"), d=s.get("device_name"): self.kill_session(u, d))
                    self.table.setCellWidget(row, 5, btn_kill)
                
        except Exception as e:
            self.logger.error(f"Error loading sessions: {e}")

    def kill_session(self, target_user, target_device):
        if PremiumMessage.question(self, MESSAGES.SESSIONS.TITLE_KILL, MESSAGES.SESSIONS.MSG_KILL_CONFIRM):
            
            if self.sync_manager.revoke_session(target_user, target_device):
                PremiumMessage.success(self, MESSAGES.SESSIONS.MSG_REVOKED, MESSAGES.SESSIONS.TEXT_REVOKED)
                self.load_sessions()
            else:
                PremiumMessage.error(self, MESSAGES.COMMON.TITLE_ERROR, MESSAGES.SESSIONS.ERR_REVOKE)
