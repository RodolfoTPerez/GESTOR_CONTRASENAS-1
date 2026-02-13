from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QWidget, QScrollArea, QFrame, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
from src.presentation.widgets.vultrax_base_card import VultraxBaseCard
from src.presentation.widgets.threat_radar import ThreatRadarWidget
from src.presentation.theme_manager import ThemeManager
from src.domain.messages import MESSAGES

class AIGuardianCard(VultraxBaseCard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(300)
        self.setProperty("depth", "dashboard")
        self._setup_ui()
        self.retranslateUi()
        self.refresh_styles()

    def _setup_ui(self):
        self.main_layout.setSpacing(12)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        # 1. TACTICAL HEADER
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title with Icon and Scanning Effect
        self.lbl_title = QLabel()
        self.lbl_title.setObjectName("ai_card_hdr_title")
        header_layout.addWidget(self.lbl_title)
        
        header_layout.addStretch()
        
        # Risk Badge
        self.lbl_risk_badge = QLabel()
        self.lbl_risk_badge.setObjectName("ai_risk_badge")
        self.lbl_risk_badge.setProperty("status", "success")
        header_layout.addWidget(self.lbl_risk_badge)
        
        # Compatibility Aliases for Dashboard
        self.lbl_ai_status = self.lbl_title
        self.lbl_dot_count = self.lbl_risk_badge
        
        self.main_layout.addWidget(header_widget)

        # 2. MAIN CONTENT SPLIT
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # Left Side: The Radar
        self.radar_container = QFrame()
        self.radar_container.setObjectName("radar_glass_nest")
        rl = QVBoxLayout(self.radar_container)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setAlignment(Qt.AlignCenter)

        self.ai_radar = ThreatRadarWidget()
        self.ai_radar.setFixedSize(190, 190)
        rl.addWidget(self.ai_radar)
        
        content_layout.addWidget(self.radar_container, 55)

        # Right Side: Intel Feed & Stats
        info_panel = QWidget()
        info_layout = QVBoxLayout(info_panel)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(12)

        # 1. Feed Header
        self.feed_hdr = QLabel("INTEL_FEED :: REAL_TIME")
        # Removing ObjectName to avoid QSS conflict, relying purely on inline style with !important
        self.feed_hdr.setStyleSheet("color: #94a3b8 !important; font-size: 11px !important; font-weight: 800 !important; letter-spacing: 1px !important; background: transparent !important;") 
        info_layout.addWidget(self.feed_hdr)

        # 2. Critical Alert Box
        self.alert_box = QFrame()
        self.alert_box.setStyleSheet("""
            QFrame {
                background-color: rgba(220, 38, 38, 0.1) !important;
                border: 1px solid rgba(220, 38, 38, 0.3) !important;
                border-radius: 6px !important;
            }
        """)
        alert_layout = QVBoxLayout(self.alert_box)
        alert_layout.setContentsMargins(12, 12, 12, 12)
        alert_layout.setSpacing(10)

        # Alert Title Row
        h_alert = QHBoxLayout()
        h_alert.setSpacing(8)
        
        # Red Dot Indicator
        dot = QLabel("●")
        dot.setStyleSheet("color: #ef4444 !important; font-size: 14px !important; background: transparent !important;")
        h_alert.addWidget(dot)

        self.lbl_alert_msg = QLabel("Critical vulnerability in 1 vaults detected")
        self.lbl_alert_msg.setStyleSheet("color: #f8fafc !important; font-size: 13px !important; font-weight: 700 !important; border: none !important; background: transparent !important;") 
        h_alert.addWidget(self.lbl_alert_msg)
        h_alert.addStretch()
        alert_layout.addLayout(h_alert)

        # Action Buttons Row
        h_btns = QHBoxLayout()
        h_btns.setSpacing(8)
        
        actions = ["APPLY", "REVIEW", "IGNORE"]
        for action in actions:
            btn = QPushButton(action)
            btn.setCursor(Qt.PointingHandCursor)
            # Standardized size 11px/12px, enforced with !important
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent !important;
                    border: 1px solid #475569 !important;
                    color: #94a3b8 !important;
                    border-radius: 4px !important;
                    padding: 4px 12px !important;
                    font-size: 11px !important;
                    font-weight: 700 !important;
                    font-family: 'Segoe UI', sans-serif !important;
                }
                QPushButton:hover {
                    border-color: #cbd5e1 !important;
                    color: #f8fafc !important;
                    background: rgba(255,255,255,0.05) !important;
                }
            """)
            h_btns.addWidget(btn)
        
        h_btns.addStretch()
        alert_layout.addLayout(h_btns)
        
        info_layout.addWidget(self.alert_box)

        # 3. Warning List
        self.warning_list_layout = QVBoxLayout()
        self.warning_list_layout.setSpacing(8)

        # DEFINE CONTENT ATOMICALLY
        warnings = [
            ("WARNING: Security posture degraded", "#fbbf24"), # Amber
            ("15 weak entropy keys identified", "#fbbf24"),
            ("1 keys found in multiple clusters", "#fbbf24")
        ]

        # Populate Layout
        for text, color in warnings:
            row = QHBoxLayout()
            row.setSpacing(8)
            
            # Icon
            icon = QLabel(">") 
            icon.setStyleSheet(f"color: {color} !important; font-weight: 900 !important; font-size: 13px !important; background: transparent !important;")
            icon.setAttribute(Qt.WA_TranslucentBackground) 
            
            # Label
            lbl = QLabel(text)
            lbl.setStyleSheet(f"color: {color} !important; font-size: 13px !important; font-weight: 600 !important; background: transparent !important;")
            lbl.setAttribute(Qt.WA_TranslucentBackground)
            
            row.addWidget(icon)
            row.addWidget(lbl)
            row.addStretch()
            self.warning_list_layout.addLayout(row)

        info_layout.addLayout(self.warning_list_layout)
        info_layout.addStretch()

        # COMPATIBILITY LAYER: Hidden ScrollArea to prevent dashboard crash
        self.scroll_ai = QScrollArea()
        self.scroll_ai.hide()
        self.ai_container = QWidget() # Also required by dashboard_ui
        self.ai_layout = QVBoxLayout(self.ai_container)        

        content_layout.addWidget(info_panel, 45)
        self.main_layout.addLayout(content_layout)

    def retranslateUi(self):
        """Universal Reactivity Hook: Refreshes labels without rebuild."""
        try:
            self.lbl_title.setText(MESSAGES.CARDS.AI_GUARDIAN_ACTIVE)
            self.lbl_risk_badge.setText(MESSAGES.CARDS.RISK_NEGLIGIBLE)
            self.feed_hdr.setText(MESSAGES.CARDS.INTEL_FEED)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Retranslate error in AIGuardianCard: {e}")

    def _add_feed_entry(self, tag, message, severity="info"):
        entry = QFrame()
        entry.setObjectName("ai_feed_entry")
        el = QVBoxLayout(entry)
        el.setContentsMargins(8, 6, 8, 6)
        el.setSpacing(2)
        
        tag_lbl = QLabel(f"> {tag}")
        tag_lbl.setObjectName(f"ai_entry_tag_{severity}")
        
        msg_lbl = QLabel(message)
        msg_lbl.setObjectName("ai_entry_msg")
        msg_lbl.setWordWrap(True)
        
        el.addWidget(tag_lbl)
        el.addWidget(msg_lbl)
        self.ai_layout.insertWidget(0, entry) # Newest at top

    def refresh_styles(self):
        """Aesthetic Encapsulation: Styling handled via QSS markers."""
        is_ghost = str(self.property("ghost")).lower() == "true"
        
        # Radar Ghost support
        if hasattr(self.ai_radar, 'setProperty'):
            self.ai_radar.setProperty("ghost", is_ghost)
            self.ai_radar.style().unpolish(self.ai_radar)
            self.ai_radar.style().polish(self.ai_radar)
            
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
