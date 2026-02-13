from PyQt5.QtWidgets import QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from src.presentation.widgets.vultrax_base_card import VultraxBaseCard
from src.presentation.widgets.tactical_metric import TacticalMetricUnit
from src.presentation.theme_manager import ThemeManager
from src.domain.messages import MESSAGES

class AuthSecurityCard(VultraxBaseCard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(300)
        self.setProperty("depth", "dashboard")
        self._setup_ui()
        self.retranslateUi()
        self.refresh_styles()

    def _setup_ui(self):
        # Use self.main_layout from VultraxBaseCard
        self.main_layout.setSpacing(4)
        self.main_layout.setAlignment(Qt.AlignTop)

        # Header
        self.auth_h = QLabel()
        self.auth_h.setObjectName("dashboard_card_title")
        self.main_layout.addWidget(self.auth_h, alignment=Qt.AlignCenter)
        self.main_layout.addSpacing(5)

        # Metrics Layout
        auth_grid = QVBoxLayout()
        auth_grid.setSpacing(4)
        auth_grid.setAlignment(Qt.AlignTop)

        self.unit_auth_mfa = TacticalMetricUnit("MFA")
        self.unit_auth_admin = TacticalMetricUnit("ADMIN", show_bar=False)
        self.unit_auth_sessions = TacticalMetricUnit("SESSIONS", show_bar=False)
        self.unit_auth_policy = TacticalMetricUnit("POLICY", show_bar=False)
        self.unit_auth_fails = TacticalMetricUnit("FAILS")
        self.unit_auth_last = TacticalMetricUnit("LAST", show_bar=False)

        # Compatibility references
        self.lbl_auth_mfa = self.unit_auth_mfa
        self.lbl_auth_admin_risk = self.unit_auth_admin
        self.lbl_auth_fails = self.unit_auth_fails
        self.lbl_auth_last_fail = self.unit_auth_last

        self.metrics = [self.unit_auth_mfa, self.unit_auth_admin, self.unit_auth_sessions, self.unit_auth_policy, self.unit_auth_fails, self.unit_auth_last]
        for u in self.metrics:
            auth_grid.addWidget(u)
        
        self.main_layout.addLayout(auth_grid)
        self.main_layout.addStretch()

        # Admin Alert Badge
        self.badge_admin_alert = QLabel()
        self.badge_admin_alert.setVisible(False)
        self.badge_admin_alert.setObjectName("admin_alert_badge")
        self.main_layout.addWidget(self.badge_admin_alert, alignment=Qt.AlignCenter)

    def retranslateUi(self):
        """Universal Reactivity Hook: Refreshes labels without rebuild."""
        try:
            self.auth_h.setText(MESSAGES.CARDS.AUTH_SECURITY)
            self.unit_auth_mfa.set_title(MESSAGES.CARDS.MFA_COVERAGE)
            self.unit_auth_admin.set_title(MESSAGES.CARDS.ADMIN_SECURITY)
            self.unit_auth_sessions.set_title(MESSAGES.CARDS.ACTIVE_SESSIONS)
            self.unit_auth_policy.set_title(MESSAGES.CARDS.SECURITY_POLICY)
            self.unit_auth_fails.set_title(MESSAGES.CARDS.LOGIN_ATTEMPTS)
            self.unit_auth_last.set_title(MESSAGES.CARDS.LAST_INCIDENT)
            self.badge_admin_alert.setText(MESSAGES.CARDS.ADMIN_UNSECURED)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Retranslate error in AuthSecurityCard: {e}")

    def refresh_styles(self):
        """Aesthetic Encapsulation: Styling handled via QSS markers."""
        is_ghost = str(self.property("ghost")).lower() == "true"
        # Cascade to units
        for u in self.metrics:
            if hasattr(u, 'setProperty'):
                u.setProperty("ghost", is_ghost)
                u.style().unpolish(u)
                u.style().polish(u)
        
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
