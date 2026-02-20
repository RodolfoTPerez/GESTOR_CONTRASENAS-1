from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame, QWidget
from PyQt5.QtCore import Qt
from src.presentation.widgets.vultrax_base_card import VultraxBaseCard
from src.presentation.widgets.circular_gauge import CircularGauge
from src.presentation.widgets.tactical_metric import TacticalMetricUnit
from src.presentation.theme_manager import ThemeManager
from src.domain.messages import MESSAGES

class SystemOverviewCard(VultraxBaseCard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(340)
        self.setProperty("depth", "dashboard")
        self._setup_ui()
        self.retranslateUi()
        self.refresh_styles()

    def _setup_ui(self):
        # Use self.main_layout from VultraxBaseCard
        self.main_layout.setSpacing(4)
        self.main_layout.setAlignment(Qt.AlignTop)

        self.lbl_h = QLabel()
        self.lbl_h.setObjectName("dashboard_card_title")
        self.main_layout.addWidget(self.lbl_h, alignment=Qt.AlignCenter)
        self.main_layout.addSpacing(2)

        # Split Layout (Left: Gauge | Right: Metrics)
        split_layout = QHBoxLayout()
        split_layout.setSpacing(25)

        # Left Side: The Gauge
        self.gauge = CircularGauge()
        self.gauge.setFixedSize(135, 135)
        split_layout.addWidget(self.gauge, 40, alignment=Qt.AlignCenter)

        # Right Side: Tactical Detail
        self.metrics_container = QFrame()
        self.metrics_container.setObjectName("tactical_metrics_box")
        ml = QVBoxLayout(self.metrics_container)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(4)

        self.unit_health = TacticalMetricUnit("HEALTH")
        self.unit_integrity = TacticalMetricUnit("INTEGRITY")
        self.unit_encryption = TacticalMetricUnit("ENCRYPTION", show_bar=False)
        self.unit_storage = TacticalMetricUnit("STORAGE", show_bar=False)
        self.unit_risk = TacticalMetricUnit("RISK", show_bar=False)
        self.unit_protocol = TacticalMetricUnit("PROTOCOL", show_bar=False)

        # Compatibility references
        self.lbl_hygiene = self.unit_health
        self.lbl_mfa = self.unit_integrity
        self.lbl_risk = self.unit_risk
        self.lbl_audit = self.unit_protocol

        for u in [self.unit_health, self.unit_integrity, self.unit_encryption, self.unit_storage, self.unit_risk, self.unit_protocol]:
            ml.addWidget(u)
        
        split_layout.addWidget(self.metrics_container, 1)
        self.main_layout.addLayout(split_layout)
        self.main_layout.addSpacing(15)

        # Sub-header for protection
        dist_container = QWidget()
        dist_l = QVBoxLayout(dist_container)
        dist_l.setContentsMargins(0, 0, 0, 0)
        dist_l.setSpacing(6)

        self.dist_head = QLabel()
        self.dist_head.setObjectName("dashboard_card_title")
        self.dist_head.setAlignment(Qt.AlignLeft)
        dist_l.addWidget(self.dist_head)

        self.bar_strength = QFrame()
        self.bar_strength.setFixedHeight(12) 
        self.bar_strength.setObjectName("bar_strength_bg")
        self.bar_strength_fill = QFrame(self.bar_strength)
        self.bar_strength_fill.setFixedHeight(12)
        self.bar_strength_fill.setObjectName("bar_strength_fill")
        
        dist_l.addWidget(self.bar_strength)
        self.main_layout.addWidget(dist_container)
        self.main_layout.addStretch()

        self.lbl_protection_status = self.dist_head

    def retranslateUi(self):
        """Universal Reactivity Hook: Refreshes labels without rebuild."""
        try:
            self.lbl_h.setText(MESSAGES.CARDS.GLOBAL_SECURITY)
            self.unit_health.set_title(MESSAGES.CARDS.SYSTEM_HEALTH)
            self.unit_integrity.set_title(MESSAGES.CARDS.AUTH_INTEGRITY)
            self.unit_encryption.set_title(MESSAGES.CARDS.ENCRYPTION_TIER)
            self.unit_storage.set_title(MESSAGES.CARDS.STORAGE_LOAD)
            self.unit_risk.set_title(MESSAGES.CARDS.RISK_EXPOSURE)
            self.unit_protocol.set_title(MESSAGES.CARDS.AUDIT_PROTOCOL)
            self.dist_head.setText(MESSAGES.CARDS.PROTECTION_STATUS)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Retranslate error in SystemOverviewCard: {e}")

    def refresh_styles(self):
        """Aesthetic Encapsulation: Styling handled via QSS markers."""
        is_ghost = str(self.property("ghost")).lower() == "true"
        
        # Cascade to tactical units if they support it
        for u in [self.unit_health, self.unit_integrity, self.unit_encryption, self.unit_storage, self.unit_risk, self.unit_protocol]:
            if hasattr(u, 'setProperty'):
                u.setProperty("ghost", is_ghost)
                u.style().unpolish(u)
                u.style().polish(u)
        
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
