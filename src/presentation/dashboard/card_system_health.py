from PyQt5.QtWidgets import QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from src.presentation.widgets.vultrax_base_card import VultraxBaseCard
from src.presentation.widgets.tactical_metric import TacticalMetricUnit
from src.domain.messages import MESSAGES

class SystemHealthCard(VultraxBaseCard):
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
        self.main_layout.addSpacing(15)

        # Metrics
        self.unit_score = TacticalMetricUnit("SCORE")
        self.unit_status = TacticalMetricUnit("STATUS", show_bar=False)
        self.unit_load = TacticalMetricUnit("LOAD")
        
        self.main_layout.addWidget(self.unit_score)
        self.main_layout.addWidget(self.unit_status)
        self.main_layout.addWidget(self.unit_load)
        self.main_layout.addStretch()

    def retranslateUi(self):
        """Universal Reactivity Hook: Refreshes labels without rebuild."""
        try:
            self.h.setText(MESSAGES.CARDS.SYSTEM_STATUS)
            self.unit_score.set_title(MESSAGES.CARDS.SECURITY_SCORE)
            self.unit_status.set_title(MESSAGES.CARDS.OP_STATUS)
            self.unit_load.set_title(MESSAGES.CARDS.SYSTEM_LOAD)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Retranslate error in SystemHealthCard: {e}")

    def refresh_styles(self):
        """Aesthetic Encapsulation: Styling handled via QSS markers."""
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
