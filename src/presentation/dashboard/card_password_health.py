from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QWidget, QGridLayout, QPushButton
from PyQt5.QtCore import Qt
from src.presentation.widgets.vultrax_base_card import VultraxBaseCard
from src.presentation.widgets.health_reactor import HealthReactorWidget
from src.presentation.theme_manager import ThemeManager
from src.domain.messages import MESSAGES

class PasswordHealthCard(VultraxBaseCard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(300)
        self.setProperty("depth", "dashboard")
        self._setup_ui()
        self.retranslateUi()
        self.refresh_styles()

    def _setup_ui(self):
        # Use self.main_layout from VultraxBaseCard
        self.main_layout.setSpacing(2)
        self.main_layout.setAlignment(Qt.AlignTop)

        # Header
        self.ph_h = QLabel()
        self.ph_h.setObjectName("dashboard_card_title")
        self.main_layout.addWidget(self.ph_h, alignment=Qt.AlignCenter)

        # Health Reactor
        self.health_reactor = HealthReactorWidget()
        self.main_layout.addWidget(self.health_reactor, alignment=Qt.AlignCenter)
        
        self.main_layout.addSpacing(12)

        # Metrics Grid
        metrics_widget = QWidget()
        metrics_l = QGridLayout(metrics_widget)
        metrics_l.setContentsMargins(0, 0, 0, 0)
        metrics_l.setSpacing(4)

        self.mini_stats_labels = {} # Store labels for retranslation

        def mk_mini_stat(icon, key, color_key):
            # key is the MESSAGES key (e.g., 'WEAK')
            w = QWidget()
            hl = QHBoxLayout(w)
            hl.setContentsMargins(0, 0, 0, 0)
            hl.setSpacing(4)
            
            ico = QLabel(icon)
            ico.setObjectName("mini_stat_icon")
            
            vl = QVBoxLayout()
            vl.setSpacing(0)
            vl.setContentsMargins(0, 0, 0, 0)
            lbl = QLabel()
            lbl.setObjectName("mini_stat_label")
            val = QLabel("0")
            val.setObjectName("mini_stat_value")
            val.setProperty("status", color_key)
            
            vl.addWidget(val)
            vl.addWidget(lbl)
            hl.addWidget(ico)
            hl.addLayout(vl)
            
            self.mini_stats_labels[key] = lbl
            return w, val

        w_weak, self.lbl_ph_weak = mk_mini_stat("🔴", "WEAK", "danger")
        w_reused, self.lbl_ph_reused = mk_mini_stat("🟡", "REUSED", "warning")
        w_strong, self.lbl_ph_strong = mk_mini_stat("🟢", "STRONG", "success")
        w_old, self.lbl_ph_old = mk_mini_stat("⏳", "EXPIRED", "text_dim")
        
        metrics_l.addWidget(w_weak, 0, 0)
        metrics_l.addWidget(w_reused, 0, 1)
        metrics_l.addWidget(w_strong, 1, 0)
        metrics_l.addWidget(w_old, 1, 1)
        
        self.main_layout.addWidget(metrics_widget)
        self.main_layout.addStretch()

        # Fix Button
        self.btn_fix_health = QPushButton()
        self.btn_fix_health.setObjectName("btn_primary_small")
        self.btn_fix_health.setCursor(Qt.PointingHandCursor)
        self.btn_fix_health.setFixedHeight(32)
        self.main_layout.addWidget(self.btn_fix_health)

    def retranslateUi(self):
        """Universal Reactivity Hook: Refreshes labels without rebuild."""
        try:
            self.ph_h.setText(MESSAGES.CARDS.PASSWORD_HEALTH)
            
            # Map internal keys to translated strings
            mapping = {
                "WEAK": MESSAGES.CARDS.WEAK,
                "REUSED": MESSAGES.CARDS.REUSED,
                "STRONG": MESSAGES.CARDS.STRONG,
                "EXPIRED": MESSAGES.CARDS.EXPIRED
            }
            for key, lbl in self.mini_stats_labels.items():
                if key in mapping:
                    lbl.setText(mapping[key])
            
            self.btn_fix_health.setText(MESSAGES.CARDS.BTN_FIX_HEALTH)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Retranslate error in PasswordHealthCard: {e}")

    def refresh_styles(self):
        """Aesthetic Encapsulation: Styling handled via QSS markers."""
        is_ghost = str(self.property("ghost")).lower() == "true"
        
        # Reactor Ghost support
        if hasattr(self.health_reactor, 'setProperty'):
            self.health_reactor.setProperty("ghost", is_ghost)
            self.health_reactor.style().unpolish(self.health_reactor)
            self.health_reactor.style().polish(self.health_reactor)
            
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
