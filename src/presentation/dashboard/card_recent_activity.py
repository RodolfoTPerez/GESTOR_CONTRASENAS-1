from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QButtonGroup, QScrollArea, QWidget
from PyQt5.QtCore import Qt
from src.presentation.widgets.vultrax_base_card import VultraxBaseCard
from src.presentation.theme_manager import ThemeManager
from src.domain.messages import MESSAGES

class RecentActivityCard(VultraxBaseCard):
    def __init__(self, current_role="user", parent=None):
        super().__init__(parent)
        self.setFixedHeight(300)
        self.setProperty("depth", "dashboard")
        self.current_role = current_role
        self._setup_ui()
        self.retranslateUi()
        self.refresh_styles()

    def _setup_ui(self):
        # Use self.main_layout from VultraxBaseCard
        self.main_layout.setSpacing(10)

        # Header with Filters
        pulse_h = QHBoxLayout()
        pulse_h.setSpacing(5)

        self.lbl_title = QLabel()
        self.lbl_title.setObjectName("dashboard_card_title")
        pulse_h.addWidget(self.lbl_title)
        pulse_h.addStretch()

        # Filters
        self.btn_filter_all = QPushButton()
        self.btn_filter_all.setCheckable(True)
        self.btn_filter_all.setChecked(True)
        
        self.btn_filter_secrets = QPushButton()
        self.btn_filter_secrets.setCheckable(True)
        
        self.btn_filter_auth = QPushButton()
        self.btn_filter_auth.setCheckable(True)
        
        self.btn_filter_admin = QPushButton()
        self.btn_filter_admin.setCheckable(True)
        
        self.btn_filter_global = QPushButton()
        self.btn_filter_global.setCheckable(True)
        
        if self.current_role.lower() != "admin":
            self.btn_filter_global.hide()

        self.filter_group = QButtonGroup(self)
        self.filter_group.setExclusive(True)

        self.filters = [self.btn_filter_all, self.btn_filter_secrets, self.btn_filter_auth, self.btn_filter_admin, self.btn_filter_global]
        for b in self.filters:
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedHeight(24)
            b.setObjectName("activity_filter_btn")
            pulse_h.addWidget(b)
            self.filter_group.addButton(b)

        self.main_layout.addLayout(pulse_h)
        self.main_layout.addSpacing(5)

        # Scroll Area
        self.scroll_activity = QScrollArea()
        self.scroll_activity.setWidgetResizable(True)
        self.scroll_activity.setObjectName("activity_scroll_area")
        self.scroll_activity.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_activity.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.activity_log_container = QWidget()
        self.activity_log_container.setObjectName("activity_container")
        self.activity_log_layout = QVBoxLayout(self.activity_log_container)
        self.activity_log_layout.setContentsMargins(0, 0, 0, 0)
        self.activity_log_layout.setSpacing(2)
        self.activity_log_layout.setAlignment(Qt.AlignTop)

        self.scroll_activity.setWidget(self.activity_log_container)
        self.main_layout.addWidget(self.scroll_activity)

    def retranslateUi(self):
        """Universal Reactivity Hook: Refreshes labels without rebuild."""
        try:
            self.lbl_title.setText(MESSAGES.CARDS.RECENT_ACTIVITY)
            self.btn_filter_all.setText(MESSAGES.CARDS.FILTER_ALL)
            self.btn_filter_secrets.setText(MESSAGES.CARDS.FILTER_VAULT)
            self.btn_filter_auth.setText(MESSAGES.CARDS.FILTER_SECURITY)
            self.btn_filter_admin.setText(MESSAGES.CARDS.FILTER_ADMIN)
            self.btn_filter_global.setText(MESSAGES.CARDS.FILTER_GLOBAL)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Retranslate error in RecentActivityCard: {e}")

    def refresh_styles(self):
        """Aesthetic Encapsulation: Styling handled via QSS markers."""
        is_ghost = str(self.property("ghost")).lower() == "true"
        
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
