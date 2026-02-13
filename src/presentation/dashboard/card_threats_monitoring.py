from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame, QWidget, QPushButton
from PyQt5.QtCore import Qt
from src.presentation.widgets.vultrax_base_card import VultraxBaseCard
from src.presentation.widgets.tactical_metric import TacticalMetricUnit
from src.domain.messages import MESSAGES

class ThreatsMonitoringCard(VultraxBaseCard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(300)
        self.setProperty("depth", "dashboard")
        self._setup_ui()
        self.retranslateUi()
        self.refresh_styles()

    def _setup_ui(self):
        self.main_layout.setSpacing(8)
        self.main_layout.setAlignment(Qt.AlignTop)

        # Header
        self.h = QLabel()
        self.h.setObjectName("dashboard_card_title")
        self.main_layout.addWidget(self.h, alignment=Qt.AlignCenter)
        self.lbl_threat_score = QLabel("0") # Tactical placeholder
        self.lbl_threat_score.hide()
        
        self.main_layout.addSpacing(10)

        # Content Split
        split = QHBoxLayout()
        
        # Left: Quick Counters
        left = QVBoxLayout()
        self.unit_active = TacticalMetricUnit("ACTIVE")
        self.unit_intel = TacticalMetricUnit("INTEL", show_bar=False)
        left.addWidget(self.unit_active)
        left.addWidget(self.unit_intel)
        left.addStretch()
        
        # Right Side: Threat Feed Container (Dynamic)
        self.threat_container = QWidget()
        self.threat_layout = QVBoxLayout(self.threat_container)
        self.threat_layout.setContentsMargins(10, 0, 0, 0)
        self.threat_layout.setSpacing(12)
        
        # 1. Feed Header
        self.lbl_feed_header = QLabel("INTEL_FEED :: REAL_TIME")
        # Removing ObjectName to avoid QSS conflict, relying purely on inline style with !important
        self.lbl_feed_header.setStyleSheet("color: #94a3b8 !important; font-size: 11px !important; font-weight: 800 !important; letter-spacing: 1px !important; background: transparent !important;") 
        self.threat_layout.addWidget(self.lbl_feed_header)

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
        
        self.threat_layout.addWidget(self.alert_box)

        # 3. Warning List
        self.warning_list_layout = QVBoxLayout()
        self.warning_list_layout.setSpacing(8)

        warnings = [
            ("WARNING: Security posture degraded", "#fbbf24"), # Amber
            ("15 weak entropy keys identified", "#fbbf24"),
            ("1 keys found in multiple clusters", "#fbbf24")
        ]

        for text, color in warnings:
            row = QHBoxLayout()
            row.setSpacing(8)
            
            icon = QLabel(">") # Chevron
            icon.setStyleSheet(f"color: {color} !important; font-weight: 900 !important; font-size: 13px !important; background: transparent !important;")
            
            lbl = QLabel(text)
            # Enforcing 13px font size
            lbl.setStyleSheet(f"color: {color} !important; font-size: 13px !important; font-weight: 600 !important; background: transparent !important;")
            
            row.addWidget(icon)
            row.addWidget(lbl)
            row.addStretch()
            self.warning_list_layout.addLayout(row)

        self.threat_layout.addLayout(self.warning_list_layout)
        self.threat_layout.addStretch()

        split.addLayout(left, 1)
        split.addWidget(self.threat_container, 2)
        
        self.main_layout.addLayout(split)
        self.main_layout.addStretch()

    def retranslateUi(self):
        """Universal Reactivity Hook: Refreshes labels without rebuild."""
        try:
            self.h.setText(MESSAGES.CARDS.THREATS_MONITORING)
            self.unit_active.set_title(MESSAGES.CARDS.ACTIVE_RISKS)
            self.unit_intel.set_title(MESSAGES.CARDS.INTEL_FEED)

        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Retranslate error in ThreatsMonitoringCard: {e}")

    def refresh_styles(self):
        """Aesthetic Encapsulation: Styling handled via QSS markers."""
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
