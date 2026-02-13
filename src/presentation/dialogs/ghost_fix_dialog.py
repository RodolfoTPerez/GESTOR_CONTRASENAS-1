from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QWidget, QGraphicsBlurEffect
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QFont, QPalette, QLinearGradient, QBrush
from src.presentation.theme_manager import ThemeManager

class GhostFixDialog(QDialog):
    """
    Ghost-style Semi-Transparent Security Dialog.
    Visualizes and resolves vault health issues with elite aesthetics.
    """
    def __init__(self, issues, secrets_manager, parent=None):
        super().__init__(parent)
        self.issues = issues # Expects {'reused': [...], 'weak': [...]}
        self.sm = secrets_manager
        self.setModal(True)
        self.setMinimumSize(700, 600)
        self.setWindowTitle("SECURITY OVERRIDE: FIX ISSUES")
        
        # Transparent background for Ghost effect
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        
        self.theme = ThemeManager()
        self.drag_pos = None
        self._setup_ui()

    def _setup_ui(self):
        colors = self.theme.get_theme_colors()
        
        # 1. Background "Ghost" Container
        self.bg_frame = QFrame(self)
        self.bg_frame.setObjectName("ghost_container")
        self.bg_frame.setStyleSheet(f"""
            QFrame#ghost_container {{
                background-color: {colors.get('ghost_bg_dark', 'rgba(15, 23, 42, 0.9)')};
                border: 2px solid {colors['primary']};
                border-radius: 20px;
            }}
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.addWidget(self.bg_frame)
        
        content_layout = QVBoxLayout(self.bg_frame)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)
        
        # 2. Header
        header = QHBoxLayout()
        title = QLabel("🛡️ SECURITY OVERRIDE")
        title.setStyleSheet(f"color: {colors['primary']}; font-family: 'Consolas'; font-size: 20px; font-weight: 900; letter-spacing: 2px;")
        header.addWidget(title)
        header.addStretch()
        
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(30, 30)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background: transparent; 
                color: {colors['text_dim']}; 
                border: none; 
                font-size: 18px; 
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: {colors['danger']}; 
                background: {colors.get('ghost_danger_10', 'rgba(255, 0, 0, 0.1)')}; 
                border-radius: 15px;
            }}
        """)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.reject)
        header.addWidget(btn_close)
        content_layout.addLayout(header)
        
        # 3. Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                border: none;
                background: {colors.get('ghost_bg', 'rgba(0,0,0,0.1)')};
                width: 6px;
                border-radius: 3px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {colors['primary']};
                min-height: 30px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {colors['accent']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 0px;
            }}
        """)
        
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(container)
        self.list_layout.setSpacing(15)
        
        self._populate_issues()
        
        scroll.setWidget(container)
        content_layout.addWidget(scroll)
        
        # 4. Footer
        footer = QLabel("PROTOCOL: FIX ALL RED VECTORS TO RESTORE SYSTEM INTEGRITY")
        footer.setStyleSheet(f"color: {colors['text_dim']}; font-family: 'Consolas'; font-size: 10px; font-weight: bold;")
        footer.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(footer)

    def _populate_issues(self):
        colors = self.theme.get_theme_colors()
        
        # --- REUSED SECTION ---
        reused = self.issues.get('reused', {})
        if reused:
            h = QLabel("🔴 DUPLICATE VECTORS (REUSED PASSWORDS)")
            h.setStyleSheet(f"color: {colors['danger']}; font-weight: bold; font-size: 13px; margin-top: 10px;")
            self.list_layout.addWidget(h)
            
            for pwd_hash, records in reused.items():
                group_box = QFrame()
                # Use theme-aware tactical color variables
                bg_col = colors.get('ghost_danger_10', 'rgba(239, 68, 68, 0.1)')
                border_col = colors.get('ghost_danger_30', 'rgba(239, 68, 68, 0.4)')
                group_box.setStyleSheet(f"background: {bg_col}; border: 1px solid {border_col}; border-radius: 12px; margin-bottom: 10px;")
                gl = QVBoxLayout(group_box)
                gl.setContentsMargins(15, 12, 15, 12)
                gl.setSpacing(10)
                
                for r in records:
                    row = QHBoxLayout()
                    info = QLabel(f"<b>{r['service']}</b> | {r['username']}")
                    info.setStyleSheet(f"color: {colors['text']}; font-size: 12px;")
                    row.addWidget(info)
                    row.addStretch()
                    
                    btn_edit = QPushButton("FIX →")
                    btn_edit.setFixedSize(100, 24)
                    btn_edit.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {colors['danger']};
                            color: {colors.get('text_on_primary', 'white')};
                            border-radius: 6px;
                            font-family: 'Consolas', 'Courier New', monospace;
                            font-size: 11px;
                            font-weight: 950;
                            border: 1px solid {colors.get('ghost_white_10', 'rgba(255, 255, 255, 0.1)')};
                        }}
                        QPushButton:hover {{
                            background-color: {colors['accent']};
                            color: {colors['text_on_primary']};
                        }}
                    """)
                    btn_edit.setCursor(Qt.PointingHandCursor)
                    btn_edit.clicked.connect(lambda _, rec=r: self._on_edit_record(rec))
                    row.addWidget(btn_edit)
                    gl.addLayout(row)
                
                self.list_layout.addWidget(group_box)

        # --- WEAK SECTION ---
        weak = self.issues.get('weak', [])
        if weak:
            h = QLabel("🟠 LOW ENTROPY VECTORS (WEAK PASSWORDS)")
            h.setStyleSheet(f"color: {colors['warning']}; font-weight: bold; font-size: 13px; margin-top: 10px;")
            self.list_layout.addWidget(h)
            
            for r in weak:
                card = QFrame()
                # Use theme-aware tactical color variables for "Weak" section
                bg_col = colors.get('ghost_warning_10', 'rgba(245, 158, 11, 0.1)')
                border_col = colors.get('ghost_warning_30', 'rgba(245, 158, 11, 0.4)')
                
                card.setStyleSheet(f"background: {bg_col}; border: 1px solid {border_col}; border-radius: 12px; margin-bottom: 8px;")
                cl = QHBoxLayout(card)
                cl.setContentsMargins(15, 8, 15, 8)
                
                info = QLabel(f"<b>{r['service']}</b> | {r['username']} (Score: {r.get('score', 0)})")
                info.setStyleSheet(f"color: {colors['text']}; font-size: 12px;")
                cl.addWidget(info)
                cl.addStretch()
                
                btn_edit = QPushButton("FIX →")
                btn_edit.setFixedSize(100, 24)
                btn_edit.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {colors['warning']};
                        color: {colors.get('text_on_primary', 'black')};
                        border-radius: 6px;
                        font-family: 'Consolas', 'Courier New', monospace;
                        font-size: 11px;
                        font-weight: 950;
                        border: 1px solid {colors.get('ghost_black_10', 'rgba(0,0,0,0.1)')};
                    }}
                    QPushButton:hover {{
                        background-color: {colors['accent']};
                        color: {colors.get('text_on_primary', 'black')};
                    }}
                """)
                btn_edit.setCursor(Qt.PointingHandCursor)
                btn_edit.clicked.connect(lambda _, rec=r: self._on_edit_record(rec))
                cl.addWidget(btn_edit)
                
                self.list_layout.addWidget(card)

        if not reused and not weak:
            empty = QLabel("✨ ALL VECTORS STABLE. NO ISSUES DETECTED.")
            empty.setStyleSheet(f"color: {colors['success']}; font-weight: bold; font-size: 14px; padding: 50px;")
            empty.setAlignment(Qt.AlignCenter)
            self.list_layout.addWidget(empty)

    def _on_edit_record(self, record):
        """Bridge to parent's edit logic."""
        self.accept()
        # Find the parent dashboard and trigger its edit row
        p = self.parent()
        while p and not hasattr(p, '_on_edit_row'):
            p = p.parent()
        
        if p:
            p._on_edit_row(record)

    def mousePressEvent(self, event):
        """Enable dragging for frameless window."""
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos is not None:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()
