from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame, QWidget, QPushButton
from PyQt5.QtCore import Qt
from src.presentation.widgets.vultrax_base_card import VultraxBaseCard
from src.presentation.widgets.tactical_metric import TacticalMetricUnit
from src.domain.messages import MESSAGES

class ThreatsMonitoringCard(VultraxBaseCard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(310)
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
        dot.setObjectName("threat_dot_indicator") # Moved style to QSS or ThemeManager
        dot.setStyleSheet("font-size: 14px; background: transparent;")
        h_alert.addWidget(dot)

        self.lbl_alert_msg = QLabel()
        self.lbl_alert_msg.setObjectName("threat_alert_msg")
        self.lbl_alert_msg.setStyleSheet("font-size: 13px; font-weight: 700; border: none; background: transparent;") 
        h_alert.addWidget(self.lbl_alert_msg)
        h_alert.addStretch()
        alert_layout.addLayout(h_alert)

        # Action Buttons Row
        self.h_btns = QHBoxLayout()
        self.h_btns.setSpacing(8)
        
        self.btn_apply = self._mk_action_btn("")
        self.btn_review = self._mk_action_btn("")
        self.btn_ignore = self._mk_action_btn("")
        
        self.h_btns.addWidget(self.btn_apply)
        self.h_btns.addWidget(self.btn_review)
        self.h_btns.addWidget(self.btn_ignore)
        self.h_btns.addStretch()
        alert_layout.addLayout(self.h_btns)
        
        self.threat_layout.addWidget(self.alert_box)

        # 3. Warning List
        self.warning_list_layout = QVBoxLayout()
        self.warning_list_layout.setSpacing(8)
        self.threat_layout.addLayout(self.warning_list_layout)
        # Content populated in retranslateUi
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

            self.lbl_alert_msg.setText(MESSAGES.AI.ALERT_CRITICAL)
            self.btn_apply.setText(MESSAGES.AI.BTN_APPLY)
            self.btn_review.setText(MESSAGES.AI.BTN_REVIEW)
            self.btn_ignore.setText(MESSAGES.AI.BTN_IGNORE)

            # Rebuild warning list
            while self.warning_list_layout.count():
                item = self.warning_list_layout.takeAt(0)
                if item.layout():
                    while item.layout().count():
                        w = item.layout().takeAt(0).widget()
                        if w: w.deleteLater()
                    item.layout().deleteLater()
                elif item.widget():
                    item.widget().deleteLater()

            warnings = [
                (MESSAGES.AI.WARN_DEGRADED, "#fbbf24"),
                (MESSAGES.AI.WARN_ENTROPY, "#fbbf24"),
                (MESSAGES.AI.WARN_CLUSTERS, "#fbbf24")
            ]
            for text, color_code in warnings:
                # [ATOMIC FIX] Use ThemeManager to get dimmed version of the warning color
                # We assume color_code is a hex string like #fbbf24
                # But to support dimming, we should use the theme's warning color if possible, 
                # or rely on the ThemeManager's apply_dimmer logic if we pass it through style tokens.
                
                # Option 1: Use specific ID and set property
                row = QHBoxLayout()
                row.setSpacing(8)
                
                # We can't easily perform QSS variable substitution here dynamically without a reload,
                # so we will use inline style BUT constructed via ThemeManager if available, 
                # or just hardcode specific class IDs and let QSS handle it.
                
                # BETTER APPROACH: Use standard classes
                icon = QLabel(">")
                icon.setObjectName("warning_icon") # Style in QSS with @warning color
                
                lbl = QLabel(text)
                lbl.setObjectName("warning_label") # Style in QSS with @warning or @text
                
                # For now, to keep the specific color, we need to manually dim it if we keep inline styles.
                # However, moving to QSS is the goal.
                # Let's try to set a property and use QSS
                icon.setProperty("status", "warning")
                lbl.setProperty("status", "warning")
                
                row.addWidget(icon); row.addWidget(lbl); row.addStretch()
                self.warning_list_layout.addLayout(row)

        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Retranslate error in ThreatsMonitoringCard: {e}")

    def refresh_styles(self):
        """Aesthetic Encapsulation: Styling handled via QSS markers."""
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
