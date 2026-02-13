from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt
from src.presentation.widgets.vultrax_base_card import VultraxBaseCard
from src.presentation.widgets.tactical_pulse_bars import TacticalPulseBars
from src.domain.messages import MESSAGES

class SecurityWatchCard(VultraxBaseCard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(300)
        self.setProperty("depth", "dashboard")
        self._setup_ui()
        self.retranslateUi()
        self.refresh_styles()

    def _setup_ui(self):
        self.main_layout.setSpacing(6)
        self.main_layout.setAlignment(Qt.AlignTop)

        # Header
        self.va_h = QLabel()
        self.va_h.setObjectName("dashboard_card_title")
        self.main_layout.addWidget(self.va_h, alignment=Qt.AlignCenter)
        self.main_layout.addSpacing(15)

        insight_layout = QHBoxLayout()
        insight_layout.setSpacing(15)

        # Left: Tactical Pulse Bars
        self.radar = TacticalPulseBars()
        self.radar.setFixedWidth(240)
        insight_layout.addWidget(self.radar)

        # Right: Intel Labels
        intel_box = QVBoxLayout()
        intel_box.setSpacing(12)
        intel_box.setAlignment(Qt.AlignVCenter)

        self.lbl_threats_info = QLabel()
        self.lbl_threats_info.setObjectName("tactical_metric_label")
        self.lbl_threats_info.setWordWrap(True)

        self.lbl_integrity_info = QLabel()
        self.lbl_integrity_info.setObjectName("tactical_metric_label")
        self.lbl_integrity_info.setWordWrap(True)

        self.lbl_va_risk = QLabel()
        self.lbl_va_risk.setObjectName("tactical_metric_label")
        self.lbl_va_unused = QLabel()
        self.lbl_va_unused.setObjectName("tactical_metric_label")
        self.lbl_va_rotation = QLabel()
        self.lbl_va_rotation.setObjectName("tactical_metric_label")
        self.lbl_va_access = QLabel()
        self.lbl_va_access.setObjectName("tactical_metric_label")

        self.intel_labels = [
            self.lbl_threats_info, self.lbl_integrity_info,
            self.lbl_va_risk, self.lbl_va_unused,
            self.lbl_va_rotation, self.lbl_va_access
        ]

        for lbl in self.intel_labels:
            intel_box.addWidget(lbl)

        insight_layout.addLayout(intel_box, 1)
        self.main_layout.addLayout(insight_layout)
        self.main_layout.addStretch()

    def retranslateUi(self):
        """Universal Reactivity Hook: Refreshes labels without rebuild."""
        try:
            self.va_h.setText(MESSAGES.CARDS.SECURITY_WATCH)
            self.lbl_threats_info.setText(MESSAGES.CARDS.STATUS_SECURE)
            self.lbl_integrity_info.setText(MESSAGES.CARDS.INTEGRITY_OPTIMAL)
            
            # Sub-metrics with icons
            self.lbl_va_risk.setText(f"🔴 {MESSAGES.CARDS.RISK}: 0.02%")
            self.lbl_va_unused.setText(f"🟡 {MESSAGES.CARDS.UNUSED}: 3")
            self.lbl_va_rotation.setText(f"🟢 {MESSAGES.CARDS.ROTATION}: OK")
            self.lbl_va_access.setText(f"🔵 {MESSAGES.CARDS.ACCESS}: LOCAL")
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Retranslate error in SecurityWatchCard: {e}")

    def refresh_styles(self):
        """Aesthetic Encapsulation: Styling handled via QSS markers."""
        is_ghost = str(self.property("ghost")).lower() == "true"
        
        # Pulse Bars Ghost support
        if hasattr(self.radar, 'setProperty'):
            self.radar.setProperty("ghost", is_ghost)
            self.radar.style().unpolish(self.radar)
            self.radar.style().polish(self.radar)
            
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
