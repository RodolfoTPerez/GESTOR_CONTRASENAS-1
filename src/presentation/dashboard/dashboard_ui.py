from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QComboBox, 
    QPushButton, QLineEdit, QTableWidget, QWidget, QSlider, 
    QCheckBox, QRadioButton, QButtonGroup, QScrollArea, QGridLayout, 
    QLayout, QStackedWidget, QGraphicsDropShadowEffect, QHeaderView,
    QProgressBar
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QDateTime, QTimer, QSize
from PyQt5.QtGui import QPixmap, QIcon, QFont, QColor, QLinearGradient
from src.domain.messages import MESSAGES
from src.presentation.ui_utils import PremiumMessage
from src.presentation.theme_manager import ThemeManager
from src.presentation.widgets.glass_card import GlassCard
from src.presentation.widgets.circular_gauge import CircularGauge
from src.presentation.widgets.identity_banner import VaultIdentityBanner
from src.presentation.widgets.radar_status import RadarStatusWidget
from src.presentation.widgets.database_status import CloudDatabaseWidget, LocalDatabaseWidget
from src.presentation.widgets.time_status import TimeSyncWidget
from src.presentation.widgets.encryption_status import EncryptionStatusWidget
from src.presentation.widgets.status_badge import StatusBadgeWidget
from src.presentation.widgets.threat_radar import ThreatRadarWidget
from src.presentation.widgets.tactical_pulse_bars import TacticalPulseBars
from src.presentation.widgets.health_reactor import HealthReactorWidget
from src.presentation.widgets.table_eye_button import TableEyeButton
from src.presentation.components.admin_panel import AdminPanel
from src.presentation.widgets.tactical_metric import TacticalMetricUnit
from src.presentation.dialogs.ghost_explanation_dialog import GhostExplanationDialog
from src.presentation.dashboard.card_system_overview import SystemOverviewCard
from src.presentation.dashboard.card_system_health import SystemHealthCard
from src.presentation.dashboard.card_auth_security import AuthSecurityCard
from src.presentation.dashboard.card_password_health import PasswordHealthCard
from src.presentation.dashboard.card_security_watch import SecurityWatchCard
from src.presentation.dashboard.card_recent_activity import RecentActivityCard
from src.presentation.dashboard.card_ai_guardian import AIGuardianCard
from src.presentation.dashboard.card_threats_monitoring import ThreatsMonitoringCard
from src.presentation.sessions_dialog import SessionsDialog
import logging

logger = logging.getLogger(__name__)

class DashboardUI:
    def _build_ui(self):
        # El estilo se aplica a nivel de QApplication en DashboardView
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        
        main_layout = QHBoxLayout(self); main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)

        # ================= SIDEBAR =================
        self.sidebar = QFrame(); self.sidebar.setObjectName("sidebar"); self.sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(self.sidebar); sidebar_layout.setContentsMargins(0, 20, 0, 20)
        
        # ================= APP BRANDING HEADER =================
        brand_card = QFrame()
        brand_card.setObjectName("brand_header")
        brand_layout = QVBoxLayout(brand_card)
        brand_layout.setContentsMargins(15, 15, 15, 15)
        brand_layout.setSpacing(5)
        
        # App Icon/Logo (Static Product Branding)
        self.app_logo_sidebar = QLabel()
        self.app_logo_sidebar.setAlignment(Qt.AlignCenter)
        
        from src.infrastructure.config.path_manager import PathManager
        default_logo = PathManager.ASSETS_DIR / "logo_v2.png" if (PathManager.ASSETS_DIR / "logo_v2.png").exists() else (PathManager.BUNDLE_DIR / "logo_v2.png")
        
        if default_logo.exists():
            pix = QPixmap(str(default_logo)).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.app_logo_sidebar.setPixmap(pix)
        else:
            self.app_logo_sidebar.setText("🛡️")
            self.app_logo_sidebar.setStyleSheet("font-size: 32px;")
        
        # App Name (Software Brand)
        app_name = QLabel("VULTRAX CORE")
        app_name.setAlignment(Qt.AlignCenter)
        app_name.setStyleSheet(self.theme.apply_tokens("""
            color: @primary;
            font-family: @font-family-main;
            font-size: 16px;
            font-weight: 800;
            letter-spacing: 2px;
        """))
        
        brand_layout.addWidget(self.app_logo_sidebar)
        brand_layout.addWidget(app_name)
        
        brand_card.setStyleSheet(self.theme.apply_tokens("""
            QFrame#brand_header {
                background: @ghost_white_5;
                border-radius: @border-radius-main;
                border: 1px solid @border;
                margin: 0 15px 15px 15px;
            }
        """))
        
        sidebar_layout.addWidget(brand_card)
        
        # Navigation separator
        nav_separator = QFrame()
        nav_separator.setFixedHeight(1)
        nav_separator.setStyleSheet(self.theme.apply_tokens("background: @border; margin: 10px 15px;"))
        sidebar_layout.addWidget(nav_separator)
        
        def add_nav(lbl, ic, idx):
            # TRENDING: High-Fidelity Navigation Styling
            btn = QPushButton(f" {ic}  {lbl}")
            btn.setObjectName("nav_btn")
            btn.setCheckable(True)
            btn.setFixedHeight(50)
            btn.setCursor(Qt.PointingHandCursor)
            
            btn.setStyleSheet(self.theme.apply_tokens("""
                QPushButton#nav_btn {
                    background: transparent;
                    color: @text_dim;
                    border: none;
                    border-radius: @border-radius-main;
                    text-align: left;
                    padding-left: 20px;
                    font-family: @font-family-main;
                    font-size: 14px;
                    font-weight: 500;
                    letter-spacing: 0.5px;
                    margin: 2px 15px;
                }
                QPushButton#nav_btn:hover {
                    background: @ghost_white_10;
                    color: @text;
                }
                QPushButton#nav_btn:checked {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                stop:0 @primary_20, 
                                stop:1 @primary_10);
                    color: @primary;
                    font-weight: 700;
                    border-left: 4px solid @primary;
                    border-radius: @border-radius-main;
                    padding-left: 16px; 
                }
            """))

            def on_nav():
                self.main_stack.setCurrentIndex(idx)
                if idx == 5: # Settings Page
                    self._load_generator_settings()
                    self._load_ui_settings()
            btn.clicked.connect(on_nav)
            self.nav_group.addButton(btn); sidebar_layout.addWidget(btn); return btn

        self.btn_nav_dashboard = add_nav("DASHBOARD", "📊", 0)
        self.btn_nav_vault = add_nav("VAULT", "🔐", 1)
        self.btn_nav_ai_side = add_nav("AI GUARDIAN", "🧠", 2)
        self.btn_nav_activity = add_nav("ACTIVITY LOG", "📜", 3)
        self.btn_nav_users = add_nav("ADMIN PANEL", "👥", 4)
        self.btn_nav_settings = add_nav("SETTINGS", "⚙️", 5)
        
        sidebar_layout.addStretch()
        
        sidebar_layout.addStretch()
        
        v_name = "VULTRAX CORE"
        # Removed local identity_banner creation from here
        
        u_card = QFrame(); u_layout = QVBoxLayout(u_card); u_layout.setContentsMargins(15, 20, 15, 10); u_layout.setSpacing(10)
        u_card.setStyleSheet(self.theme.apply_tokens("background: @ghost_white_5; border-radius: @border-radius-main; border-top: 1px solid @ghost_white_10;"))
        
        self.lbl_user_info = QLabel(f"👤 {self.current_username.upper()}")
        self.lbl_user_info.setStyleSheet(self.theme.apply_tokens("color: @text; font-family: @font-family-main; font-size: 13px; font-weight: 600; letter-spacing: 1px;"))
        
        logout_row = QHBoxLayout()
        self.btn_logout = QPushButton("🚪")
        self.btn_logout.setFixedSize(32, 32)
        self.btn_logout.setObjectName("btn_logout_premium")
        self.btn_logout.setCursor(Qt.PointingHandCursor)
        self.btn_logout.setStyleSheet(self.theme.apply_tokens("""
            QPushButton#btn_logout_premium {
                background: @danger_20;
                color: @danger;
                border: 1px solid @danger_30;
                border-radius: 10px;
                font-size: 14px;
            }
            QPushButton#btn_logout_premium:hover {
                background: @danger_40;
                border-color: @danger;
            }
        """))
        self.btn_logout.clicked.connect(self.logout)
        
        logout_row.addWidget(self.lbl_user_info); logout_row.addStretch(); logout_row.addWidget(self.btn_logout)
        
        u_layout.addLayout(logout_row)
        # self.status_encryption MOVED TO HEADER Row 1
        sidebar_layout.addWidget(u_card)
        # (Sidebar addition moved to the end of _build_ui for right-side placement)

        # ================= MAIN CONTENT =================
        content_box = QWidget(); content_layout = QVBoxLayout(content_box); content_layout.setContentsMargins(0,0,0,0); content_layout.setSpacing(0)
        
        # --- HUD: INFRASTRUCTURE STATUS WIDGETS (CORE TELEMETRY) ---
        self.status_internet = RadarStatusWidget()
        self.status_supabase = CloudDatabaseWidget()
        self.status_sqlite = LocalDatabaseWidget()
        self.status_encryption = EncryptionStatusWidget()
        self.status_encryption.setToolTip("Estado de Cifrado: AES-256 GCM activo (Capa de Seguridad Estática)")
        self.status_sync_badge = StatusBadgeWidget("🔄")
        self.status_audit_badge = StatusBadgeWidget("🛡️")
        self.lbl_countdown = TimeSyncWidget()
        
        self.status_internet.setToolTip(MESSAGES.TACTICAL.TOOLTIP_INTERNET)
        self.status_supabase.setToolTip(MESSAGES.TACTICAL.TOOLTIP_SUPABASE)
        self.status_sqlite.setToolTip(MESSAGES.TACTICAL.TOOLTIP_SQLITE)

        # --- HUD: UNIFIED TOP BAR (SEARCH + TELEMETRY) ---
        self.header = QFrame(); self.header.setObjectName("dashboard_header"); self.header.setFixedHeight(140)
        self.header.setStyleSheet(self.theme.apply_tokens("""
            #dashboard_header {
                background: @bg_sec_60;
                border: none;
                border-bottom-left-radius: 30px;
                border-bottom-right-radius: 30px;
            }
            #dashboard_header[user_mode="true"] {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 @ghost_white_5, stop:1 @ghost_white_10);
                border-bottom: 2px solid @ghost_white_10;
            }
        """))
        
        h_shadow = QGraphicsDropShadowEffect(self.header)
        h_shadow.setBlurRadius(40); h_shadow.setXOffset(0); h_shadow.setYOffset(10)
        h_shadow.setColor(QColor(0, 0, 0, 100))
        self.header.setGraphicsEffect(h_shadow)
        
        # Main Header Layout (Vertical)
        header_v_layout = QVBoxLayout(self.header)
        header_v_layout.setContentsMargins(30, 20, 30, 20)
        header_v_layout.setSpacing(10)
        # --- ROW 1: STATUS BADGE + SEARCH + TELEMETRY ---
        row1_layout = QHBoxLayout()
        row1_layout.setContentsMargins(0, 0, 0, 0)
        row1_layout.setSpacing(15)

        # 1. Encryption Badge (Left)
        row1_layout.addWidget(self.status_encryption)
        row1_layout.addStretch()

        # --- ROW 2: ENLARGED VAULT IDENTITY ---
        row2_layout = QHBoxLayout()
        row2_layout.setContentsMargins(0, 5, 0, 0)
        row2_layout.setSpacing(15)

        from src.infrastructure.config.path_manager import PathManager
        custom_logo = PathManager.DATA_DIR / "custom_logo.png"
        default_logo = PathManager.ASSETS_DIR / "logo_v2.png" if (PathManager.ASSETS_DIR / "logo_v2.png").exists() else (PathManager.BUNDLE_DIR / "logo_v2.png")
        actual_logo = custom_logo if custom_logo.exists() else default_logo

        self.lbl_v_icon = QLabel()
        if actual_logo.exists():
            pix = QPixmap(str(actual_logo)).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.lbl_v_icon.setPixmap(pix)
        else:
            self.lbl_v_icon.setText("🛡️")
            self.lbl_v_icon.setStyleSheet("font-size: 32px;")
        
        # 1. Identity Banner (Corporate Brand)
        self.lbl_v_name = QLabel()
        self.lbl_v_name.setObjectName("lbl_v_name")
        
        # Load identity from DB Meta (Synchronized) with QSettings fallback
        db_name = None
        if hasattr(self, 'sm') and self.sm:
            db_name = self.sm.get_meta("instance_name")
            
        if not db_name:
            from PyQt5.QtCore import QSettings
            from src.presentation.theme_manager import ThemeManager
            settings = QSettings(ThemeManager.APP_ID, "VultraxCore_Global")
            db_name = settings.value("company_name", "IT SECURITY")
            
        self.lbl_v_name.setText(str(db_name).upper())
        self.lbl_v_name.setStyleSheet(self.theme.apply_tokens("color: @text; font-size: 48px; font-weight: 900; letter-spacing: 3px; background: transparent; padding-bottom: 5px; font-family: @font-family-main;"))
        
        row2_layout.addWidget(self.lbl_v_icon)
        row2_layout.addWidget(self.lbl_v_name)
        row2_layout.addStretch()

        # 2. HUD SEARCH
        self.hud_search_box = QFrame(); self.hud_search_box.setObjectName("hud_search_box")
        self.hud_search_box.setFixedWidth(280); self.hud_search_box.setFixedHeight(34)
        self.hud_search_box.setStyleSheet("border-radius: 14px;")
        h_search_layout = QHBoxLayout(self.hud_search_box); h_search_layout.setContentsMargins(0, 0, 0, 0)
        
        self.dash_search = QLineEdit()
        self.dash_search.setPlaceholderText(MESSAGES.TACTICAL.SEARCH_HUD)
        self.dash_search.setObjectName("dash_search_input")
        h_search_layout.addWidget(self.dash_search)
        row1_layout.addWidget(self.hud_search_box)
        
        # 3. ACTION BUTTON (REMOVED as per user request)
        # self.btn_add_dash = QPushButton("＋ NEW")
        # self.btn_add_dash.setObjectName("btn_add_premium"); self.btn_add_dash.setFixedSize(80, 34)
        # self.btn_add_dash.setStyleSheet("border-radius: 14px;")
        # row1_layout.addWidget(self.btn_add_dash)
        
        # 4. TELEMETRY CLUSTER (Right Aligned)
        row1_layout.addWidget(self.status_internet)
        row1_layout.addWidget(self.status_supabase)
        row1_layout.addWidget(self.status_sqlite)
        row1_layout.addWidget(self.lbl_countdown)
        
        header_v_layout.addLayout(row1_layout)
        header_v_layout.addLayout(row2_layout)
        
        content_layout.addWidget(self.header)

        # 2. SESSION PROTECTION LAYER
        self.session_bar = QProgressBar()
        self.session_bar.setFixedSize(120, 4)
        self.session_bar.setTextVisible(False)
        self.session_bar.setObjectName("session_protection_bar")
        self.session_bar.setToolTip(MESSAGES.TACTICAL.TOOLTIP_SESSION)
        
        # --- GHOST MODE TOGGLE (Moved to Sidebar or integrated) ---
        self.ghost_enabled = False
        self.btn_ghost_toggle = QPushButton("👻")
        self.btn_ghost_toggle.setFixedSize(42, 42)
        self.btn_ghost_toggle.setObjectName("btn_ghost_toggle")
        self.btn_ghost_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_ghost_toggle.setToolTip(MESSAGES.TACTICAL.TOOLTIP_GHOST)
        self.btn_ghost_toggle.clicked.connect(self._toggle_ghost_mode)

        # Add session and ghost controls to sidebar
        sb_wrap = QHBoxLayout(); sb_wrap.setContentsMargins(15, 0, 15, 15); sb_wrap.setSpacing(12)
        
        self.session_bar.setStyleSheet(self.theme.apply_tokens("""
            QProgressBar#session_protection_bar {
                background: @ghost_white_5;
                border: none;
                border-radius: 2px;
            }
            QProgressBar#session_protection_bar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 @success, stop:1 @success_dim);
                border-radius: 2px;
            }
        """))
        
        self.btn_ghost_toggle.setStyleSheet(self.theme.apply_tokens("""
            QPushButton#btn_ghost_toggle {
                background: @ghost_white_5;
                border: 1px solid @ghost_white_10;
                border-radius: @border-radius-main;
                font-size: 16px;
            }
            QPushButton#btn_ghost_toggle:hover {
                background: @ghost_white_10;
                border-color: @ghost_white_30;
            }
        """))
        
        sb_wrap.addWidget(self.session_bar)
        sb_wrap.addStretch()
        sb_wrap.addWidget(self.btn_ghost_toggle)
        sidebar_layout.addLayout(sb_wrap)
        
        # STACK & VIEWS
        self.main_stack = QStackedWidget()
        self.view_dashboard = self._module_dashboard() 
        self.view_vault = self._module_vault()         
        self.view_ai = self._module_ai()
        self.view_activity = self._module_activity()
        self.view_users = self._module_admin()
        self.view_settings = self._module_settings()

        for v in [self.view_dashboard, self.view_vault, self.view_ai, self.view_activity, self.view_users, self.view_settings]: self.main_stack.addWidget(v)
        content_layout.addWidget(self.main_stack)
        
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(content_box)
        
        self.btn_nav_dashboard.setChecked(True); self.main_stack.setCurrentIndex(0)
        self.status_sync = QLabel(); self.status_datetime = QLabel()

    def _module_dashboard(self):
        page = QWidget()
        scroll = QScrollArea(page); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame); scroll.setObjectName("dashboard_scroll")
        container = QWidget()
        container.setObjectName("bento_container")
        layout = QVBoxLayout(container); layout.setContentsMargins(35, 5, 35, 5); layout.setSpacing(4)
 
        # (Identity Banner removed from here, now it is Global Top Header in _build_ui)

        # (Widget Bar removed to gain vertical space, integrated in Global Header)

        # --- GLOBAL SECURITY WARNING (Enterprise Standard) ---
        self.global_security_banner = GlassCard()
        self.global_security_banner.setObjectName("global_security_banner")
        self.global_security_banner.setFixedHeight(60)
        self.global_security_banner.hide() # Hidden by default
        
        banner_inner = QHBoxLayout(self.global_security_banner)
        banner_inner.setContentsMargins(20, 0, 20, 0)
        
        self.lbl_banner_msg = QLabel(MESSAGES.TACTICAL.BANNER_MFA)
        self.lbl_banner_msg.setObjectName("global_warning_label")
        
        banner_inner.addWidget(self.lbl_banner_msg, alignment=Qt.AlignCenter)
        layout.addWidget(self.global_security_banner)

        # (Controls moved to right-side sidebar)
        
        # --- BENTO GRID (VULTRAX 12-COLUMN ARCHITECTURE) ---
        grid = QGridLayout()
        grid.setSpacing(18) # Gutter: 18 px (Reduced from 24 for compact view)
        
        # Standard 12-Column Stretch
        for i in range(12):
            grid.setColumnStretch(i, 1)
        
        # 1.a SYSTEM OVERVIEW (Vultrax Core: Fila Crítica 8 cols)
        self.card_system_overview = SystemOverviewCard()
        self.card_system_overview.doubleClicked.connect(self._show_system_overview_explanation)
        
        # Mapping tactical references for DashboardView compatibility
        self.gauge = self.card_system_overview.gauge
        self.unit_health = self.card_system_overview.unit_health
        self.unit_integrity = self.card_system_overview.unit_integrity
        self.unit_encryption = self.card_system_overview.unit_encryption
        self.unit_storage = self.card_system_overview.unit_storage
        self.unit_risk = self.card_system_overview.unit_risk
        self.unit_protocol = self.card_system_overview.unit_protocol
        self.lbl_hygiene = self.unit_health # Alias
        self.lbl_mfa = self.unit_integrity # Alias
        self.lbl_risk = self.unit_risk # Alias
        self.lbl_audit = self.unit_protocol # Alias
        self.bar_strength = self.card_system_overview.bar_strength
        self.bar_strength_fill = self.card_system_overview.bar_strength_fill
        self.lbl_protection_status = self.card_system_overview.lbl_protection_status
        
        grid.addWidget(self.card_system_overview, 1, 0, 1, 6) 

        # 1c. SYSTEM HEALTH (Operational Slot 1)
        self.card_system_health = SystemHealthCard()
        self.card_system_health.doubleClicked.connect(self._show_system_explanation)  # ✅ Ghost Dialog
        # Aliases for telemetry wiring
        self.unit_score = self.card_system_health.unit_score
        self.unit_status = self.card_system_health.unit_status
        self.unit_load = self.card_system_health.unit_load
        
        grid.addWidget(self.card_system_health, 2, 0, 1, 3)
        
        # 1b. AUTH SECURITY (Operational Slot 2)
        self.card_auth = AuthSecurityCard()
        self.card_auth.doubleClicked.connect(self._show_auth_explanation)
        
        # Performance/Status mapping
        self.unit_auth_mfa = self.card_auth.unit_auth_mfa
        self.unit_auth_admin = self.card_auth.unit_auth_admin
        self.unit_auth_sessions = self.card_auth.unit_auth_sessions
        self.unit_auth_policy = self.card_auth.unit_auth_policy
        self.unit_auth_fails = self.card_auth.unit_auth_fails
        self.unit_auth_last = self.card_auth.unit_auth_last
        self.lbl_auth_mfa = self.card_auth.lbl_auth_mfa
        self.lbl_auth_admin_risk = self.card_auth.lbl_auth_admin_risk
        self.lbl_auth_fails = self.card_auth.lbl_auth_fails
        self.lbl_auth_last_fail = self.card_auth.lbl_auth_last_fail
        self.badge_admin_alert = self.card_auth.badge_admin_alert
        
        grid.addWidget(self.card_auth, 2, 3, 1, 3) # Fila operativa: 3 cols
        
        # 2. INFO TILES (Cyber-Ops Metrics)
        def mk_info_tile(title_key, icon, color):
            c = GlassCard()
            c.setFixedHeight(85) # Taller for better spacing
            c.setProperty("depth", "dashboard")
            c.setObjectName("premium_info_tile")
            
            cl = QVBoxLayout(c)
            cl.setContentsMargins(20, 12, 20, 12)
            cl.setSpacing(4)
            
            # Header with Icon and Label
            hl = QHBoxLayout()
            hl.setSpacing(10)
            
            ic = QLabel(icon)
            ic.setObjectName("tile_icon_glow")
            ic.setStyleSheet(f"font-size: 18px;")
            
            tit = QLabel(MESSAGES.INFO_TILES.get(title_key, title_key))
            tit.setObjectName("tile_title_tactical")
            tit.setStyleSheet(self.theme.apply_tokens(f"color: @text_dim; font-family: @font-family-main; font-size: 10px; font-weight: bold; letter-spacing: 1.5px; opacity: 0.6;"))
            
            hl.addWidget(ic)
            hl.addWidget(tit)
            hl.addStretch()
            cl.addLayout(hl)
            
            # Save for retranslation
            c.title_label = tit
            c.title_key = title_key
            
            # Large Value
            val = QLabel("0")
            val.setObjectName("info_tile_value")
            val.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            val.setStyleSheet(self.theme.apply_tokens(f"color: @text; font-family: @font-family-main; font-size: 24px; font-weight: 800;"))
            
            # Subtle Progress/Decoration underline
            line = QFrame()
            line.setFixedHeight(2)
            line.setStyleSheet(f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {color}, stop:1 transparent); border-radius: 1px;")
            
            cl.addWidget(val)
            cl.addWidget(line)
            
            # Interactivity Style (Now handled in QSS)
            pass
            
            return c, val

        if self.current_role == "admin":
            # ADMIN INFO TILES (Global System Metrics)
            self.card_admin, self.stat_admin_val = mk_info_tile("ADMIN SECRETS", "🏢", "#3b82f6")
            self.card_others, self.stat_others_val = mk_info_tile("USERS SECRETS", "👥", "#0ea5e9")
            self.card_users, self.stat_users_val = mk_info_tile("TOTAL USERS", "👤", "#06b6d4")
            self.card_sessions, self.stat_sessions_val = mk_info_tile("SESSIONS", "⚡", "#8b5cf6")
            self.card_logs, self.stat_logs_val = mk_info_tile("LOGS", "📜", "#f59e0b")
            
            tiles_layout = QHBoxLayout(); tiles_layout.setSpacing(15)
            tiles_layout.addWidget(self.card_admin)
            tiles_layout.addWidget(self.card_others)
            tiles_layout.addWidget(self.card_users)
            tiles_layout.addWidget(self.card_sessions)
            tiles_layout.addWidget(self.card_logs)
        else:
            # USER INFO TILES (Personal Metrics)
            self.card_total, self.stat_total_val = mk_info_tile("LBL_TOTAL", "🔑", "#3b82f6")
            self.card_weak, self.stat_weak_val = mk_info_tile("LBL_WEAK", "⚠️", "#ef4444")
            self.card_age, self.stat_age_val = mk_info_tile("LBL_AGE", "📅", "#f59e0b")

            tiles_layout = QHBoxLayout(); tiles_layout.setSpacing(25)
            tiles_layout.addWidget(self.card_total); tiles_layout.addWidget(self.card_weak); tiles_layout.addWidget(self.card_age)
        
        # Las mini-cards superiores (Info Tiles)
        grid.addLayout(tiles_layout, 0, 0, 1, 12)

        # 3. PASSWORD HEALTH
        self.card_health = PasswordHealthCard()
        self.card_health.doubleClicked.connect(self._show_health_explanation)
        
        # Critical health refs
        self.health_reactor = self.card_health.health_reactor
        self.lbl_ph_weak = self.card_health.lbl_ph_weak
        self.lbl_ph_reused = self.card_health.lbl_ph_reused
        self.lbl_ph_strong = self.card_health.lbl_ph_strong
        self.lbl_ph_old = self.card_health.lbl_ph_old
        self.btn_fix_health = self.card_health.btn_fix_health
        
        grid.addWidget(self.card_health, 2, 6, 1, 3) # 3 cols
        
        # 4. SECURITY WATCH
        self.card_analytics = SecurityWatchCard()
        self.card_analytics.doubleClicked.connect(self._show_security_watch_explanation)
        
        # Operational watch refs
        self.radar = self.card_analytics.radar
        self.lbl_threats_info = self.card_analytics.lbl_threats_info
        self.lbl_integrity_info = self.card_analytics.lbl_integrity_info
        self.lbl_va_risk = self.card_analytics.lbl_va_risk
        self.lbl_va_unused = self.card_analytics.lbl_va_unused
        self.lbl_va_rotation = self.card_analytics.lbl_va_rotation
        self.lbl_va_access = self.card_analytics.lbl_va_access
        
        grid.addWidget(self.card_analytics, 2, 9, 1, 3) # 3 cols

        # 7. AI GUARDIAN
        self.card_ai_guardian = AIGuardianCard()
        self.card_ai_guardian.doubleClicked.connect(self._show_ai_guardian_explanation)
        # Tactical Feed mapping
        self.lbl_ai_status = self.card_ai_guardian.lbl_ai_status
        self.lbl_dot_count = self.card_ai_guardian.lbl_dot_count
        self.scroll_ai = self.card_ai_guardian.scroll_ai
        self.ai_container = self.card_ai_guardian.ai_container
        self.ai_layout = self.card_ai_guardian.ai_layout
        self.ai_radar = self.card_ai_guardian.ai_radar
        
        grid.addWidget(self.card_ai_guardian, 1, 6, 1, 6) # 6 cols (Balanced 50/50 with Overview)

        # 5. QUICK ACTIONS
        self.actions_card = GlassCard(); self.actions_card.setFixedHeight(84); self.actions_card.setProperty("depth", "dashboard")
        al = QHBoxLayout(self.actions_card); al.setContentsMargins(20,0,20,0); al.setSpacing(12)
        
        def mk_quick_btn(icon, text_key, col_key):
            text = MESSAGES.QUICK_ACTIONS.get(text_key, text_key)
            b = QPushButton(f"{icon} {text}")
            b.setFixedHeight(54)
            b.setCursor(Qt.PointingHandCursor)
            b.setObjectName("quick_action_btn")
            b.setProperty("btn_type", col_key)
            # Store for retranslation
            b.quick_icon = icon
            b.quick_key = text_key
            return b

        if self.current_role == "admin":
            self.btn_go_vault = mk_quick_btn("👥", "QA_USERS", "primary")
            self.btn_go_activity = mk_quick_btn("📜", "QA_AUDIT", "ai_sec")
            self.btn_go_monitor = mk_quick_btn("📡", "QA_MONITOR", "primary")
            self.btn_go_ai = mk_quick_btn("🛡️", "QA_INTEGRITY", "ai")
            self.btn_go_sync = mk_quick_btn("🔄", "QA_SYNC", "success")
            self.btn_go_services = mk_quick_btn("💎", "QA_SERVICES", "primary")
            quick_btns = [self.btn_go_vault, self.btn_go_activity, self.btn_go_monitor, self.btn_go_ai, self.btn_go_sync, self.btn_go_services]
        else:
            self.btn_go_vault = mk_quick_btn("🔐", "QA_VAULT", "primary")
            self.btn_go_activity = mk_quick_btn("📜", "QA_HISTORY", "ai_sec")
            # MONITOR hidden for non-admin
            self.btn_go_ai = mk_quick_btn("🧠", "QA_AI_SCAN", "ai")
            self.btn_go_sync = mk_quick_btn("🔄", "QA_SYNC", "success")
            self.btn_go_services = mk_quick_btn("➕", "QA_SERVICES", "primary")
            quick_btns = [self.btn_go_vault, self.btn_go_activity, self.btn_go_ai, self.btn_go_sync, self.btn_go_services]
        
        for b in quick_btns: al.addWidget(b)
        
        grid.addWidget(self.actions_card, 3, 0, 1, 12)

        # --- BARRA FLOTANTE (DASHBOARD) ---
        self.float_bar_dashboard = QFrame()
        self.float_bar_dashboard.setObjectName("float_bar_dashboard")
        self.float_bar_dashboard.setFixedHeight(0)
        # Styles moved to QSS
        pass
        
        layout.addLayout(grid)
        # Removed stretch to return to original layout
        
        scroll.setWidget(container)
        
        # Estructura Horizontal (Full Width)
        h_box = QHBoxLayout()
        h_box.setContentsMargins(0,0,0,0); h_box.setSpacing(0)
        h_box.addWidget(scroll, 1)
        
        # Estructura Vertical Final de la Página
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0,0,0,0); page_layout.setSpacing(0)
        page_layout.addLayout(h_box, 1)
        page_layout.addWidget(self.float_bar_dashboard, 0)
        
        # Objetos técnicos necesarios para compatibilidad
        self.table = QTableWidget(self); self.table.hide()
        self.btn_add = QPushButton(self); self.btn_add.hide()
        self.btn_sync = QPushButton(self); self.btn_sync.hide()
        self.btn_delete = QPushButton(self); self.btn_delete.hide()
        return page

    def _show_system_overview_explanation(self):
        """Show Ghost Dialog for System Overview Metrics"""
        # Determine strict text values
        health_txt = str(self.gauge.value) # Use raw int value
        integrity_txt = self.unit_integrity.lbl_value.text()
        enc_txt = self.unit_encryption.lbl_value.text()
        store_txt = self.unit_storage.lbl_value.text()
        risk_txt = self.unit_risk.lbl_value.text()
        audit_txt = self.unit_protocol.lbl_value.text()
        
        data = {
            MESSAGES.EXPLANATIONS.SYS_HEALTH: health_txt,
            MESSAGES.EXPLANATIONS.SYS_INTEGRITY: integrity_txt,
            MESSAGES.EXPLANATIONS.SYS_ENCRYPTION: enc_txt,
            MESSAGES.EXPLANATIONS.SYS_STORAGE: store_txt,
            MESSAGES.EXPLANATIONS.SYS_RISK: risk_txt,
            MESSAGES.EXPLANATIONS.SYS_PROTOCOL: audit_txt
        }
        
        dlg = GhostExplanationDialog(MESSAGES.EXPLANATIONS.TITLE_SYSTEM, data, self)
        # Center on screen or over dashboard? Center on screen is safer for now.
        # Ideally center over parent window.
        dlg.move(self.window().frameGeometry().center() - dlg.rect().center())
        dlg.exec_()

    def _show_auth_explanation(self):
        """Ghost Dialog for Auth Security"""
        # Gather data from TacticalMetricUnits in Auth Card
        data = {
            MESSAGES.EXPLANATIONS.AUTH_MFA: self.unit_auth_mfa.lbl_value.text(),
            MESSAGES.EXPLANATIONS.AUTH_ADMIN: self.unit_auth_admin.lbl_value.text(),
            MESSAGES.EXPLANATIONS.AUTH_SESSIONS: self.unit_auth_sessions.lbl_value.text(),
            MESSAGES.EXPLANATIONS.AUTH_POLICY: self.unit_auth_policy.lbl_value.text(),
            MESSAGES.EXPLANATIONS.AUTH_FAILS: self.unit_auth_fails.lbl_value.text()
        }
        dlg = GhostExplanationDialog(MESSAGES.EXPLANATIONS.TITLE_AUTH, data, self)
        dlg.move(self.window().frameGeometry().center() - dlg.rect().center())
        dlg.exec_()

    def _show_health_explanation(self):
        """Ghost Dialog for Password Health"""
        data = {
            MESSAGES.EXPLANATIONS.HEALTH_SCORE: str(self.health_reactor.health_score),
            MESSAGES.EXPLANATIONS.HEALTH_WEAK: self.lbl_ph_weak.text(),
            MESSAGES.EXPLANATIONS.HEALTH_REUSED: self.lbl_ph_reused.text(),
            MESSAGES.EXPLANATIONS.HEALTH_EXPIRED: self.lbl_ph_old.text(),
            MESSAGES.EXPLANATIONS.HEALTH_STRONG: self.lbl_ph_strong.text()
        }
        dlg = GhostExplanationDialog(MESSAGES.EXPLANATIONS.TITLE_HEALTH, data, self)
        dlg.move(self.window().frameGeometry().center() - dlg.rect().center())
        dlg.exec_()

    def _show_security_watch_explanation(self):
        """Ghost Dialog for Security Watch"""
        data = {
            MESSAGES.EXPLANATIONS.WATCH_STATUS: self.lbl_threats_info.text(),
            MESSAGES.EXPLANATIONS.WATCH_INTEGRITY: self.lbl_integrity_info.text(),
            MESSAGES.EXPLANATIONS.WATCH_RISK: self.lbl_va_risk.text(), 
            MESSAGES.EXPLANATIONS.WATCH_ACCESS: self.lbl_va_access.text(),
            MESSAGES.EXPLANATIONS.WATCH_POLICY: self.lbl_va_rotation.text()
        }
        dlg = GhostExplanationDialog(MESSAGES.EXPLANATIONS.TITLE_WATCH, data, self)
        dlg.move(self.window().frameGeometry().center() - dlg.rect().center())
        dlg.exec_()

    def _show_activity_explanation(self):
        """Ghost Dialog for Activity Log"""
        data = {
            MESSAGES.EXPLANATIONS.ACT_SOURCE: MESSAGES.EXPLANATIONS.VAL_ACT_SQLITE,
            MESSAGES.EXPLANATIONS.ACT_FREQ: MESSAGES.EXPLANATIONS.VAL_ACT_NORMAL,
            MESSAGES.EXPLANATIONS.ACT_STATUS: MESSAGES.EXPLANATIONS.VAL_ACT_RECORDING,
            MESSAGES.EXPLANATIONS.ACT_TYPES: MESSAGES.EXPLANATIONS.VAL_ACT_TYPES_ALL
        }
        dlg = GhostExplanationDialog(MESSAGES.EXPLANATIONS.TITLE_ACTIVITY, data, self)
        dlg.move(self.window().frameGeometry().center() - dlg.rect().center())
        dlg.exec_()

    def _show_ai_guardian_explanation(self):
        """Ghost Dialog for AI Guardian with Concept Definitions"""
        if not hasattr(self, 'card_ai_guardian'): return
        
        # Get live values and labels from Radar
        radar_vals = self.card_ai_guardian.ai_radar._values
        radar_labels = self.card_ai_guardian.ai_radar._labels
        
        # 1. CORE STATS (Top Section)
        data = {
            MESSAGES.EXPLANATIONS.AI_STATUS: self.card_ai_guardian.lbl_ai_status.text(),
            MESSAGES.EXPLANATIONS.AI_RISKS: self.card_ai_guardian.lbl_dot_count.text(),
            MESSAGES.EXPLANATIONS.AI_LATENCY: MESSAGES.EXPLANATIONS.VAL_AI_LATENCY_12,
            MESSAGES.EXPLANATIONS.AI_MODEL: MESSAGES.EXPLANATIONS.VAL_AI_MODEL_V4
        }
        
        # 2. SECTOR DEFINITIONS (Main Request)
        # We add a header for the definitions section using the INTERP_RADAR description
        data[MESSAGES.EXPLANATIONS.AI_SECTOR_HEAD] = MESSAGES.EXPLANATIONS.INTERP_RADAR
        
        # Map each label to its percentage AND its definition
        for i in range(len(radar_labels)):
            label = radar_labels[i]
            val = f"{radar_vals[i]}%"
            
            # Key format: "Sector: NAME (Value%)"
            # This allows the dialog's _interpret_metric to find the keyword "NAME"
            key = f"{MESSAGES.EXPLANATIONS.AI_SECTOR}: {label} ({val})"
            data[key] = val

        dlg = GhostExplanationDialog(MESSAGES.EXPLANATIONS.TITLE_AI, data, self)
        dlg.move(self.window().frameGeometry().center() - dlg.rect().center())
        dlg.exec_()

    def _show_system_explanation(self):
        """Ghost Dialog for System Health Card"""
        # Gather data from TacticalMetricUnits in System Health Card
        data = {
            MESSAGES.EXPLANATIONS.SYS_SCORE: MESSAGES.EXPLANATIONS.DESC_SYS_SCORE,
            MESSAGES.EXPLANATIONS.SYS_STATUS: MESSAGES.EXPLANATIONS.DESC_SYS_STATUS,
            MESSAGES.EXPLANATIONS.SYS_LOAD: MESSAGES.EXPLANATIONS.DESC_SYS_LOAD
        }
        dlg = GhostExplanationDialog(MESSAGES.EXPLANATIONS.TITLE_HEALTH_SYS, data, self)
        dlg.move(self.window().frameGeometry().center() - dlg.rect().center())
        dlg.exec_()

    def _toggle_ghost_mode(self):
        """Alterna entre estética sólida y translúcida (Ghost Mode)"""
        # [THEME GUARD: STRICT CODE VALIDATION]
        # We check the authoritative codes from ThemeManager
        theme_code = self.settings.value("theme_active", "tactical_dark")
        from src.presentation.theme_manager import ThemeManager
        if ThemeManager._GLOBAL_THEME:
            theme_code = ThemeManager._GLOBAL_THEME
            
        # "cyber_arctic" is the internal code for the Light Theme
        # [THEME GUARD] Light Themes don't support Ghost Mode (Visual Artifacts)
        # We silently ignore the click or force disable without annoying popups
        if theme_code in ["cyber_arctic", "bunker_ops"] or "light" in theme_code.lower():
            self.ghost_enabled = False
            # Reset visual state just in case
            self.btn_ghost_toggle.setProperty("active", "false")
            self.btn_ghost_toggle.style().unpolish(self.btn_ghost_toggle)
            self.btn_ghost_toggle.style().polish(self.btn_ghost_toggle)
            logger.info(f"GhostMode: Action ignored due to incompatible theme: {theme_code}")
            return

        self.ghost_enabled = not self.ghost_enabled
        state_str = "true" if self.ghost_enabled else "false"
        
        # Icono constante pero cambiamos el estilo visual del botón
        self.btn_ghost_toggle.setProperty("active", state_str)
        self.btn_ghost_toggle.style().unpolish(self.btn_ghost_toggle)
        self.btn_ghost_toggle.style().polish(self.btn_ghost_toggle)
        
        # Propagar la propiedad a absolutamente todos los widgets
        self.setProperty("ghost", state_str)
        
        # [SENIOR SYNC] Propagate property and explicitly check card members
        target_cards = [
            'card_system_overview', 'card_system_health', 'card_auth', 
            'card_health', 'card_analytics', 'card_ai_guardian',
            'card_recent_activity', 'card_threats_monitoring'
        ]
        
        # Fast propagation using recursive findChildren
        for w in self.findChildren(QWidget):
            w.setProperty("ghost", state_str)
            
            # [SENIOR MODULAR FIX] Call refresh_styles if available
            if hasattr(w, 'refresh_styles'):
                try:
                    w.refresh_styles()
                except:
                    pass

            w.style().unpolish(w)
            w.style().polish(w)
            w.update()
            
        # Explicit Force for member cards (Verification Layer)
        for attr in target_cards:
            if hasattr(self, attr):
                card = getattr(self, attr)
                if card:
                    card.setProperty("ghost", state_str)
                    if hasattr(card, 'refresh_styles'): card.refresh_styles()
                    card.style().unpolish(card)
                    card.style().polish(card)
        
        logger.info(f"GhostMode ({state_str}): Dynamic property sync completed in fast path.")
        
        # Refrescar la ventana principal y los stacks
        if hasattr(self, 'main_stack'):
            self.main_stack.update()
            # Also refresh current widget explicitly
            if self.main_stack.currentWidget():
                self.main_stack.currentWidget().update()
        
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def _module_vault(self):
        page = QWidget(); l = QVBoxLayout(page); l.setContentsMargins(35, 25, 35, 35); l.setSpacing(20)
        # In Module Vault, we use a simpler header or the sidebar banner
        # self.identity_banner_vault = VaultIdentityBanner(v_name, show_badge=False)
        # l.addWidget(self.identity_banner_vault)

        header = QHBoxLayout(); title = QLabel("🔐 VAULT MANAGEMENT"); title.setObjectName("vault_title_label")
        self.search_vault = QLineEdit(); 
        self.search_vault.setPlaceholderText("🔍 Search credentials..."); self.search_vault.setFixedWidth(260); self.search_vault.setObjectName("search_bar")
        header.addWidget(self.search_vault)

        self.btn_voice_search = QPushButton("🎤")
        self.btn_voice_search.setFixedSize(30, 30)
        self.btn_voice_search.setCursor(Qt.PointingHandCursor)
        self.btn_voice_search.setObjectName("btn_voice_search")
        self.btn_voice_search.setToolTip("Voice Search")
        self.btn_voice_search.setStyleSheet(self.theme.apply_tokens("""
            QPushButton#btn_voice_search {
                background: @ghost_white_5;
                border: 1px solid @secondary_30;
                border-radius: 15px;
                color: @secondary;
                font-size: 14px;
            }
            QPushButton#btn_voice_search:hover {
                background: @secondary_10;
                border: 1px solid @secondary;
            }
            QPushButton#btn_voice_search[listening="true"] {
                background: @danger_20;
                border: 1px solid @danger;
                color: @danger;
            }
        """))
        header.addWidget(self.btn_voice_search)
        self.lbl_vault_search_count = QLabel("")
        self.lbl_vault_search_count.setObjectName("vault_badge_counter")
        self.lbl_vault_search_count.setFixedHeight(24)
        self.lbl_vault_search_count.setStyleSheet(self.theme.apply_tokens("""
            QLabel#vault_badge_counter {
                background: @secondary_10;
                color: @secondary;
                font-family: @font-family-main;
                font-size: 10px;
                font-weight: 800;
                padding: 0 12px;
                border: 1px solid @secondary_30;
                border-radius: 12px;
                letter-spacing: 1px;
                margin-left: 15px;
            }
        """))
        header.addWidget(self.lbl_vault_search_count)
        header.addStretch()
        
        self.btn_import = QPushButton("⬆️"); self.btn_export = QPushButton("⬇️"); self.btn_template = QPushButton("📄")
        self.btn_import.setCursor(Qt.PointingHandCursor); self.btn_export.setCursor(Qt.PointingHandCursor); self.btn_template.setCursor(Qt.PointingHandCursor)
        self.btn_import.setObjectName("vault_action_btn"); self.btn_export.setObjectName("vault_action_btn"); self.btn_template.setObjectName("vault_action_btn")
        
        self.btn_import.setToolTip("Import Data")
        self.btn_export.setToolTip("Export Data")
        self.btn_template.setToolTip("Template import Data")
        
        header.addWidget(self.btn_import); header.addWidget(self.btn_export); header.addWidget(self.btn_template); header.addSpacing(12)
        
        self.btn_add_vault = QPushButton("  ➕  NEW CREDENTIAL  "); self.btn_add_vault.setCursor(Qt.PointingHandCursor); self.btn_add_vault.setObjectName("btn_add_vault")
        header.addWidget(self.btn_add_vault); l.addLayout(header)
        
        t_card = GlassCard(); tl = QVBoxLayout(t_card); tl.setContentsMargins(1,1,1,1)
        self.table_vault = QTableWidget(0, 10)
        self.table_vault.setAlternatingRowColors(False)  # CRITICAL: Disable OS colors!
        self.table_vault.verticalHeader().setVisible(False)
        self.table_vault.setShowGrid(False)
        self.table_vault.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_vault.setHorizontalHeaderLabels(["○", "LVL", "SYNC", "SERVICE", "PROPIETARIO", "ANTIGÜEDAD", "NOTAS", "PASSWORD", "ACCIONES", "STATUS"])
        
        # DARK MODE SAAS - ULTRA DARK (PREMIUM SLATE)
        # TABLE STYLING DELEGATED TO QSS (dashboard.qss)
        self.table_vault.setObjectName("vault_table") 
        
        hhv = self.table_vault.horizontalHeader(); hhv.setSectionResizeMode(QHeaderView.Fixed)
        self.table_vault.setColumnWidth(0, 45)  # Selection
        self.table_vault.setColumnWidth(1, 65)  # LVL (Emoji + text)
        self.table_vault.setColumnWidth(2, 75)  # SYNC (Emoji + text)
        self.table_vault.setColumnWidth(3, 220) # SERVICE
        self.table_vault.setColumnWidth(4, 150) # PROPIETARIO
        self.table_vault.setColumnWidth(5, 130) # ANTIGÜEDAD (Full word)
        self.table_vault.setColumnWidth(6, 300) # NOTAS (More space)
        self.table_vault.setColumnWidth(7, 280) # PASSWORD
        self.table_vault.setColumnWidth(8, 120) # ACCIONES
        self.table_vault.setColumnWidth(9, 100) # STATUS
        tl.addWidget(self.table_vault); self.side_panel_vault = QWidget(); self.side_panel_vault.setObjectName("side_detail_panel_vault"); self.side_panel_vault.hide()
        
        table_vault_with_panel = QHBoxLayout()
        table_vault_with_panel.setContentsMargins(0, 0, 0, 0)
        table_vault_with_panel.setSpacing(0)
        table_vault_with_panel.addWidget(t_card, stretch=1)
        
        self.side_panel_vault = QWidget()
        self.side_panel_vault.setObjectName("side_detail_panel_vault")
        self.side_panel_vault.setFixedWidth(400)
        self.side_panel_vault.hide()
        table_vault_with_panel.addWidget(self.side_panel_vault, stretch=0)
        
        l.addLayout(table_vault_with_panel, 1)
        
        # --- BARRA FLOTANTE (VAULT) ---
        self.float_bar_vault = QFrame()
        self.float_bar_vault.setObjectName("float_bar_vault")
        self.float_bar_vault.setFixedHeight(0)
        
        fb_layout = QHBoxLayout(self.float_bar_vault)
        fb_layout.setContentsMargins(35, 0, 35, 0)
        fb_layout.setSpacing(15)
        
        self.lbl_vault_selection_status = QLabel("0 NODOS SELECCIONADOS"); self.lbl_vault_selection_status.setObjectName("float_status_label")
        self.lbl_vault_selection_status.setStyleSheet(self.theme_manager.apply_tokens("color: @text_dim; font-family: @font-family-main; font-weight: 800; font-size: 11px;"))
        fb_layout.addWidget(self.lbl_vault_selection_status)
        fb_layout.addStretch()
        
        def mk_fb_btn(text, obj_name):
            b = QPushButton(text); b.setObjectName(obj_name); b.setCursor(Qt.PointingHandCursor)
            b.setFixedHeight(34); b.setFixedWidth(120)
            b.setStyleSheet(self.theme_manager.apply_tokens("font-family: @font-family-main; font-weight: 800; font-size: 11px;"))
            return b
            
        self.btn_vault_view = mk_fb_btn("👁️  VIEW", "btn_float_view")
        self.btn_vault_copy = mk_fb_btn("📋  COPY", "btn_float_copy")
        self.btn_vault_edit = mk_fb_btn("✏️  EDIT", "btn_float_edit")
        self.btn_vault_delete = mk_fb_btn("🗑️  DELETE", "btn_float_delete")
        self.btn_vault_delete.setStyleSheet(self.theme_manager.apply_tokens("background: @ghost_danger_15; color: @danger; border: 1px solid @danger; font-family: @font-family-main; font-weight: 800; font-size: 11px;"))
        
        self.btn_vault_deselect = mk_fb_btn("✖️  DESELECT", "btn_float_deselect")
        self.btn_vault_deselect.setStyleSheet(self.theme_manager.apply_tokens("background: @ghost_text_dim_15; color: @text_dim; border: 1px solid @text_dim; font-family: @font-family-main; font-weight: 800; font-size: 11px;"))
        
        fb_layout.addWidget(self.btn_vault_deselect)
        fb_layout.addWidget(self.btn_vault_view)
        fb_layout.addWidget(self.btn_vault_copy)
        fb_layout.addWidget(self.btn_vault_edit)
        fb_layout.addWidget(self.btn_vault_delete)
        
        l.addWidget(self.float_bar_vault, 0)

        self.btn_sync_vault = QPushButton("🔄 SYNC VAULT"); self.btn_sync_vault.setFixedWidth(250)
        self.btn_sync_vault.setCursor(Qt.PointingHandCursor); self.btn_sync_vault.setObjectName("btn_sync_vault")
        v_actions = QHBoxLayout()
        v_actions.addStretch(); v_actions.addWidget(self.btn_sync_vault); l.addLayout(v_actions)
        return page

    def _module_ai(self):
        page = QWidget(); layout = QHBoxLayout(page); layout.setContentsMargins(40, 40, 40, 40); layout.setSpacing(30)
        core_card = GlassCard(); cl = QVBoxLayout(core_card); cl.setAlignment(Qt.AlignCenter); cl.setSpacing(18)

        core_lbl = QLabel("🧠"); core_lbl.setObjectName("ai_core_icon"); cl.addWidget(core_lbl)
        cl.addWidget(QLabel("AI GUARDIAN", objectName="ai_module_title"))
        cl.addWidget(QLabel("Neural Security Analysis", objectName="ai_module_subtitle"))
        layout.addWidget(core_card, 1); ops_card = GlassCard(); ol = QVBoxLayout(ops_card); ol.setContentsMargins(45, 45, 45, 45); ol.setSpacing(22)
        ol.addWidget(QLabel("🔍 OPERATIONS", objectName="ai_ops_title"))
        ol.addWidget(QLabel("Run intelligent analysis to detect weak patterns and security vulnerabilities in your vault.", objectName="ai_ops_desc"))
        self.btn_ai_invoke = QPushButton("  ⚡  START AI SCAN  "); self.btn_ai_invoke.setFixedHeight(60); self.btn_ai_invoke.setCursor(Qt.PointingHandCursor)
        self.btn_ai_invoke.setObjectName("btn_ai_invoke")
        ol.addWidget(self.btn_ai_invoke); ol.addStretch(); console = QLabel("> System ready\n> AI neural network initialized\n> Awaiting command..."); console.setObjectName("ai_console")
        ol.addWidget(console); layout.addWidget(ops_card, 2)
        return page

    def _module_activity(self):
        page = QWidget(); l = QVBoxLayout(page); l.setContentsMargins(35, 30, 35, 35); l.setSpacing(25)
        h = QHBoxLayout(); t = QLabel("📜 ACTIVITY LOG"); t.setObjectName("activity_log_title")
        self.btn_refresh_audit_cloud = QPushButton("   🔄   SYNC HISTORY   ")
        self.btn_refresh_audit_cloud.setCursor(Qt.PointingHandCursor); self.btn_refresh_audit_cloud.setObjectName("btn_sync_logs")
        h.addWidget(t); h.addStretch(); h.addWidget(self.btn_refresh_audit_cloud); l.addLayout(h)
        # --- BARRA DE FILTROS INTEGRADAS ---
        f_row = QHBoxLayout(); f_row.setSpacing(10)
        self.btn_mod_all = QPushButton("ALL"); self.btn_mod_all.setCheckable(True); self.btn_mod_all.setChecked(True)
        self.btn_mod_auth = QPushButton("AUTH"); self.btn_mod_auth.setCheckable(True)
        self.btn_mod_sec = QPushButton("SECRETS"); self.btn_mod_sec.setCheckable(True)
        self.btn_mod_adm = QPushButton("ADMIN"); self.btn_mod_adm.setCheckable(True)
        self.btn_mod_global = QPushButton("🌐 GLOBAL CLOUD"); self.btn_mod_global.setCheckable(True)
        
        self.mod_filter_group = QButtonGroup(self); self.mod_filter_group.setExclusive(True)
        
        mod_filters = [self.btn_mod_all, self.btn_mod_auth, self.btn_mod_sec, self.btn_mod_adm, self.btn_mod_global]
        for b in mod_filters:
            b.setCursor(Qt.PointingHandCursor); b.setFixedHeight(30); b.setObjectName("activity_filter_btn")
            b.setStyleSheet(self.theme_manager.apply_tokens("""
                QPushButton { background: @ghost_white_08; color: @text_dim; font-size: 11px; font-weight: 700; border: 1px solid @border; border-radius: 6px; padding: 0 15px; font-family: @font-family-main; }
                QPushButton:checked { background: @ghost_info_15; color: @info; border: 1px solid @info; }
                QPushButton:hover { background: @ghost_white_15; }
            """))
            f_row.addWidget(b)
            self.mod_filter_group.addButton(b)
        
        f_row.addStretch()
        l.addLayout(f_row)

        t_card = GlassCard(); tl = QVBoxLayout(t_card); tl.setContentsMargins(1,1,1,1)
        self.table_audit = QTableWidget(0, 7)
        self.table_audit.setAlternatingRowColors(False)  # CRITICAL: Disable OS colors!
        self.table_audit.verticalHeader().setVisible(False)
        self.table_audit.verticalHeader().setDefaultSectionSize(38) # Aumentar altura de fila para legibilidad
        self.table_audit.setShowGrid(False)
        headers = ["TIMESTAMP", "USER", "ACTION", "TARGET", "DEVICE", "DETAILS", "STATUS"]
        self.table_audit.setHorizontalHeaderLabels(headers)
        
        
        # DARK MODE SAAS - ULTRA DARK (NO WHITE/GREY EVER!)
        # TABLE STYLING DELEGATED TO QSS (dashboard.qss)
        self.table_audit.setObjectName("audit_table") # Optional: specific ID if needed
        
        hh = self.table_audit.horizontalHeader(); hh.setSectionResizeMode(QHeaderView.Interactive); hh.resizeSection(0, 170); hh.resizeSection(1, 100); hh.resizeSection(2, 130); hh.resizeSection(3, 180); hh.resizeSection(4, 180); hh.setSectionResizeMode(5, QHeaderView.Stretch); hh.resizeSection(6, 120)
        tl.addWidget(self.table_audit); l.addWidget(t_card)
        return page

    def _module_admin(self):
        """
        Instancia y configura el Panel de Administración modular.
        """
        self.admin_panel = AdminPanel(
            sm=self.sm,
            um=self.user_manager,
            sync_manager=self.sync_manager,
            current_username=self.current_username,
            parent=self
        )
        # Exponer botones internos para compatibilidad si es necesario o manejarlos directamente
        # En este caso, el componente ya maneja sus propias señales internas.
        return self.admin_panel

    def _module_settings(self):
        container = QWidget()
        main_v = QVBoxLayout(container)
        main_v.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setObjectName("settings_scroll_area")
        
        page = QWidget()
        page.setObjectName("settings_page")
        l = QVBoxLayout(page)
        l.setContentsMargins(50, 40, 50, 70)
        l.setSpacing(25)
        
        # Header
        h = QHBoxLayout()
        t = QLabel(MESSAGES.SETTINGS.HEADER)
        t.setObjectName("settings_title")
        h.addWidget(t)
        h.addStretch()
        l.addLayout(h)
        l.addSpacing(15)
        
        
        # ============================================================
        # CARD 1: INTERFAZ OPERATIVA
        # ============================================================
        # Category Header (Outside card)
        interface_header = QLabel("🌐 " + MESSAGES.SETTINGS.SEC_INTERFACE.upper())
        interface_header.setObjectName("settings_category_label")
        l.addWidget(interface_header)
        
        # Card with settings only
        interface_card = GlassCard()
        interface_card.setProperty("depth", "settings")
        interface_l = QVBoxLayout(interface_card)
        interface_l.setContentsMargins(30, 25, 30, 25)
        interface_l.setSpacing(18)
        
        # Idioma
        lang_row = QHBoxLayout()
        lang_row.setSpacing(15)
        lang_label = QLabel("🌐 " + MESSAGES.SETTINGS.LBL_LANG.upper())
        lang_label.setObjectName("settings_label")
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(MESSAGES.LISTS.LANGUAGES)
        self.combo_lang.setFixedWidth(200)
        self.combo_lang.setObjectName("settings_combo")
        # [LOOP FIX] Removed currentIndexChanged connection here. 
        # It's handled by 'activated' in DashboardView to avoid loops during init.
        lang_row.addWidget(lang_label)
        lang_row.addStretch()
        lang_row.addWidget(self.combo_lang)
        interface_l.addLayout(lang_row)
        
        # Tema
        theme_row = QHBoxLayout()
        theme_row.setSpacing(15)
        theme_label = QLabel("🎨 " + MESSAGES.SETTINGS.LBL_THEME.upper())
        theme_label.setObjectName("settings_label")
        self.combo_theme = QComboBox()
        self.combo_theme.addItems(MESSAGES.LISTS.THEMES)
        self.combo_theme.setFixedWidth(200)
        self.combo_theme.setObjectName("settings_combo")
        # [LOOP FIX] Removed currentIndexChanged connection here.
        # It's handled by 'activated' in DashboardView.
        theme_row.addWidget(theme_label)
        theme_row.addStretch()
        theme_row.addWidget(self.combo_theme)
        interface_l.addLayout(theme_row)
        
        # Auto-bloqueo
        lock_row = QHBoxLayout()
        lock_row.setSpacing(15)
        lock_label = QLabel("⏱️ " + MESSAGES.SETTINGS.LBL_AUTO_LOCK.upper())
        lock_label.setObjectName("settings_label")
        self.combo_lock_time = QComboBox()
        self.combo_lock_time.addItems(MESSAGES.LISTS.LOCK_TIMES)
        self.combo_lock_time.setFixedWidth(200)
        self.combo_lock_time.setObjectName("settings_combo")
        self.combo_lock_time.activated.connect(self._on_lock_time_changed)
        lock_row.addWidget(lock_label)
        lock_row.addStretch()
        lock_row.addWidget(self.combo_lock_time)
        interface_l.addLayout(lock_row)
        
        l.addWidget(interface_card)

        # ============================================================
        # CARD 7: PERSONALIZACIÓN & BRANDING
        # ============================================================
        branding_header = QLabel("🎨 " + MESSAGES.SETTINGS.SEC_BRANDING.upper())
        branding_header.setObjectName("settings_category_label")
        l.addWidget(branding_header)

        branding_card = GlassCard()
        branding_card.setProperty("depth", "settings")
        branding_l = QVBoxLayout(branding_card)
        branding_l.setContentsMargins(30, 25, 30, 25)
        branding_l.setSpacing(18)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(15)
        brand_info = QVBoxLayout()
        brand_info.setSpacing(4)
        brand_title = QLabel("🏢 " + MESSAGES.SETTINGS.LBL_BRANDING.upper())
        brand_title.setObjectName("settings_label")
        brand_desc = QLabel(MESSAGES.SETTINGS.DESC_BRANDING)
        brand_desc.setObjectName("settings_desc")
        brand_info.addWidget(brand_title)
        brand_info.addWidget(brand_desc)

        # --- Dynamic Company Name Field ---
        current_company = None
        if hasattr(self, 'sm') and self.sm:
            current_company = self.sm.get_meta("instance_name")
            
        if not current_company:
            from PyQt5.QtCore import QSettings
            from src.presentation.theme_manager import ThemeManager
            settings = QSettings(ThemeManager.APP_ID, "VultraxCore_Global")
            current_company = settings.value("company_name", "IT SECURITY")

        company_row = QHBoxLayout()
        lbl_comp_name = QLabel(MESSAGES.SETTINGS.LBL_COMPANY_NAME)
        lbl_comp_name.setObjectName("settings_label_small")
        lbl_comp_name.setStyleSheet("font-size: 11px; color: @text_dim;")
        
        self.txt_company_name = QLineEdit(current_company)
        self.txt_company_name.setObjectName("settings_input_branding")
        self.txt_company_name.setFixedWidth(200)
        self.txt_company_name.setStyleSheet(self.theme.apply_tokens("""
            QLineEdit#settings_input_branding {
                background: @ghost_white_5;
                border: 1px solid @border;
                border-radius: 6px;
                padding: 4px 10px;
                color: @text;
                font-family: @font-family-main;
            }
        """))
        
        company_row.addWidget(lbl_comp_name)
        company_row.addWidget(self.txt_company_name)
        company_row.addStretch()
        
        # Logo Preview Container
        preview_container = QFrame()
        preview_container.setFixedSize(60, 60)
        preview_container.setObjectName("logo_preview_container")
        preview_container.setStyleSheet("background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px;")
        
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(2, 2, 2, 2)
        
        self.lbl_logo_preview = QLabel()
        self.lbl_logo_preview.setAlignment(Qt.AlignCenter)
        
        # Load current logo for preview
        from src.infrastructure.config.path_manager import PathManager
        custom_logo = PathManager.DATA_DIR / "custom_logo.png"
        default_logo = PathManager.ASSETS_DIR / "logo_v2.png" if (PathManager.ASSETS_DIR / "logo_v2.png").exists() else (PathManager.BUNDLE_DIR / "logo_v2.png")
        
        actual_logo = custom_logo if custom_logo.exists() else default_logo
        if actual_logo.exists():
            pix = QPixmap(str(actual_logo)).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.lbl_logo_preview.setPixmap(pix)
        else:
            self.lbl_logo_preview.setText("🛡️")
            self.lbl_logo_preview.setStyleSheet("font-size: 20px; color: @text_dim;")
            
        preview_layout.addWidget(self.lbl_logo_preview)

        self.btn_change_logo = QPushButton(MESSAGES.SETTINGS.BTN_CHANGE_LOGO)
        self.btn_change_logo.setCursor(Qt.PointingHandCursor)
        self.btn_change_logo.setObjectName("btn_settings_action")
        self.btn_change_logo.setFixedWidth(150)
        
        brand_row.addLayout(brand_info)
        brand_row.addStretch()
        brand_row.addWidget(preview_container)
        brand_row.addWidget(self.btn_change_logo)
        branding_l.addLayout(brand_row)
        branding_l.addLayout(company_row)

        l.addWidget(branding_card)
        
        # ============================================================
        # CARD 2: SEGURIDAD DE NÚCLEO
        # ============================================================
        # Category Header (Outside card)
        security_header = QLabel("🔐 " + MESSAGES.SETTINGS.SEC_CORE.upper())
        security_header.setObjectName("settings_category_label")
        l.addWidget(security_header)
        
        # Card with settings only
        security_card = GlassCard()
        security_card.setProperty("depth", "settings")
        security_l = QVBoxLayout(security_card)
        security_l.setContentsMargins(30, 25, 30, 25)
        security_l.setSpacing(18)
        
        # Firma Maestra
        master_row = QHBoxLayout()
        master_row.setSpacing(15)
        master_info = QVBoxLayout()
        master_info.setSpacing(4)
        master_title = QLabel("🔑 " + MESSAGES.SETTINGS.LBL_MASTER_SIG.upper())
        master_title.setObjectName("settings_label")
        master_desc = QLabel(MESSAGES.SETTINGS.DESC_MASTER_SIG)
        master_desc.setObjectName("settings_desc")
        master_info.addWidget(master_title)
        master_info.addWidget(master_desc)
        self.btn_change_pwd_real = QPushButton(MESSAGES.SETTINGS.BTN_MOD)
        self.btn_change_pwd_real.setCursor(Qt.PointingHandCursor)
        self.btn_change_pwd_real.setObjectName("btn_settings_action")
        self.btn_change_pwd_real.setFixedWidth(150)
        master_row.addLayout(master_info)
        master_row.addStretch()
        master_row.addWidget(self.btn_change_pwd_real)
        security_l.addLayout(master_row)
        
        # Integridad de Bóveda
        vault_row = QHBoxLayout()
        vault_row.setSpacing(15)
        vault_info = QVBoxLayout()
        vault_info.setSpacing(4)
        vault_title = QLabel("🛠️ " + MESSAGES.SETTINGS.LBL_VAULT_INTEGRITY.upper())
        vault_title.setObjectName("settings_label")
        vault_desc = QLabel(MESSAGES.SETTINGS.DESC_VAULT_INTEGRITY)
        vault_desc.setObjectName("settings_desc")
        vault_info.addWidget(vault_title)
        vault_info.addWidget(vault_desc)
        self.btn_repair_vault_dashboard = QPushButton(MESSAGES.SETTINGS.BTN_REP)
        self.btn_repair_vault_dashboard.setCursor(Qt.PointingHandCursor)
        self.btn_repair_vault_dashboard.setObjectName("btn_settings_repair")
        self.btn_repair_vault_dashboard.setFixedWidth(150)
        vault_row.addLayout(vault_info)
        vault_row.addStretch()
        vault_row.addWidget(self.btn_repair_vault_dashboard)
        security_l.addLayout(vault_row)
        
        l.addWidget(security_card)
        
        # ============================================================
        # CARD 3: GENERADOR DE CONTRASEÑAS
        # ============================================================
        # Category Header (Outside card)
        gen_header = QLabel("🔑 " + MESSAGES.SETTINGS.SEC_GENERATOR.upper())
        gen_header.setObjectName("settings_category_label")
        l.addWidget(gen_header)
        
        # Card with settings only
        gen_card = GlassCard()
        gen_card.setProperty("depth", "settings")
        gen_main_l = QVBoxLayout(gen_card)
        gen_main_l.setContentsMargins(30, 25, 30, 25)
        gen_main_l.setSpacing(20)
        
        # Longitud
        saved_len = self.settings.value("length", 20, type=int)
        len_l = QHBoxLayout()
        l_len_tit = QLabel("📏 " + MESSAGES.SETTINGS.LBL_SEC_LENGTH.upper())
        l_len_tit.setObjectName("generator_label")
        len_l.addWidget(l_len_tit)
        self.length_label = QLabel(str(saved_len))
        self.length_label.setObjectName("generator_value")
        len_l.addStretch()
        len_l.addWidget(self.length_label)
        gen_main_l.addLayout(len_l)
        
        self.length_slider = QSlider(Qt.Horizontal)
        self.length_slider.setObjectName("generator_slider")
        self.length_slider.setRange(8, 64)
        self.length_slider.setValue(saved_len)
        self.length_slider.valueChanged.connect(self._on_length_changed)
        gen_main_l.addWidget(self.length_slider)
        
        # Complejidad
        comp_l = QHBoxLayout()
        comp_l.setSpacing(20)
        
        def mk_cb(txt, key_name, default_val=True):
            cb = QCheckBox(txt)
            cb.setCursor(Qt.PointingHandCursor)
            cb.setObjectName("generator_checkbox")
            is_checked = str(self.settings.value(key_name, default_val)).lower() in ("true", "1")
            cb.setChecked(is_checked)
            cb.stateChanged.connect(self._save_generator_settings)
            return cb
        
        self.cb_upper = mk_cb(MESSAGES.DASHBOARD.GEN_UPPER.upper(), "upper")
        self.cb_lower = mk_cb(MESSAGES.DASHBOARD.GEN_LOWER.upper(), "lower")
        self.cb_digits = mk_cb(MESSAGES.DASHBOARD.GEN_DIGITS.upper(), "digits")
        self.cb_symbols = mk_cb(MESSAGES.DASHBOARD.GEN_SYMBOLS.upper(), "symbols")
        comp_l.addWidget(self.cb_upper)
        comp_l.addWidget(self.cb_lower)
        comp_l.addWidget(self.cb_digits)
        comp_l.addWidget(self.cb_symbols)
        gen_main_l.addLayout(comp_l)
        
        # Botón Generar
        self.btn_generate_advanced = QPushButton(MESSAGES.SETTINGS.BTN_GENERATE_ADV)
        self.btn_generate_advanced.setCursor(Qt.PointingHandCursor)
        self.btn_generate_advanced.setFixedHeight(50)
        self.btn_generate_advanced.setObjectName("btn_generate_advanced")
        self.btn_generate_advanced.clicked.connect(self._generate_password_advanced)
        gen_main_l.addWidget(self.btn_generate_advanced)
        
        l.addWidget(gen_card)
        
        # ============================================================
        # CARD 4: INTELIGENCIA ESTRATÉGICA (IA)
        # ============================================================
        # Category Header (Outside card)
        ai_header = QLabel("🧠 " + MESSAGES.SETTINGS.LBL_INTEL_STRAT.upper())
        ai_header.setObjectName("settings_category_label")
        l.addWidget(ai_header)
        
        # Card with settings only
        ai_card = GlassCard()
        ai_card.setProperty("depth", "settings")
        ail = QVBoxLayout(ai_card)
        ail.setContentsMargins(30, 25, 30, 25)
        ail.setSpacing(18)
        
        # Provider Row
        provider_row = QHBoxLayout()
        provider_row.setSpacing(15)
        provider_label = QLabel("⚙️ " + MESSAGES.SETTINGS.LBL_PROVIDOR_STRAT.upper())
        provider_label.setObjectName("settings_label")
        self.combo_provider = QComboBox()
        self.combo_provider.addItems(MESSAGES.LISTS.AI_PROVIDERS)
        self.combo_provider.setFixedWidth(210)
        self.combo_provider.setObjectName("ai_combo_provider")
        provider_row.addWidget(provider_label)
        provider_row.addStretch()
        provider_row.addWidget(self.combo_provider)
        ail.addLayout(provider_row)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(self.theme.apply_tokens("background-color: @ghost_white_10; max-height: 1px;"))
        ail.addWidget(separator)
        
        # Keys Section Label
        keys_label = QLabel("API Keys (Las 3 se guardan simultáneamente)")
        keys_label.setStyleSheet(self.theme.apply_tokens("color: @text_dim; font-size: 11px; font-weight: 600;"))
        ail.addWidget(keys_label)
        
        # All 3 Keys in Vertical Layout
        def mk_key_in(ph):
            s = QLineEdit()
            s.setPlaceholderText(ph)
            s.setEchoMode(QLineEdit.Password)
            s.setObjectName("ai_key_input")
            return s
        
        self.input_key_gemini = mk_key_in("AIza...")
        self.input_key_chatgpt = mk_key_in("sk...")
        self.input_key_claude = mk_key_in("sk-ant...")
        
        # Gemini
        gemini_label = QLabel("Google Gemini")
        gemini_label.setStyleSheet("font-weight: 600; font-size: 11px; margin-top: 8px;")
        ail.addWidget(gemini_label)
        ail.addWidget(self.input_key_gemini)
        
        # ChatGPT
        chatgpt_label = QLabel("OpenAI ChatGPT")
        chatgpt_label.setStyleSheet("font-weight: 600; font-size: 11px; margin-top: 8px;")
        ail.addWidget(chatgpt_label)
        ail.addWidget(self.input_key_chatgpt)
        
        # Claude
        claude_label = QLabel("Anthropic Claude")
        claude_label.setStyleSheet("font-weight: 600; font-size: 11px; margin-top: 8px;")
        ail.addWidget(claude_label)
        ail.addWidget(self.input_key_claude)
        
        # Save Button
        self.btn_save_settings = QPushButton(MESSAGES.SETTINGS.BTN_SAVE_AI)
        self.btn_save_settings.setCursor(Qt.PointingHandCursor)
        self.btn_save_settings.setObjectName("btn_save_ai_settings")
        ail.addWidget(self.btn_save_settings)
        
        l.addWidget(ai_card)
        
        # ============================================================
        # CARD 5: HERRAMIENTAS DE PROMPT
        # ============================================================
        # Category Header (Outside card)
        prompt_header = QLabel("💬 " + MESSAGES.SETTINGS.LBL_PROMPT.upper())
        prompt_header.setObjectName("settings_category_label")
        l.addWidget(prompt_header)
        
        # Card with settings only
        prompt_card = GlassCard()
        prompt_card.setProperty("depth", "settings")
        prompt_l = QVBoxLayout(prompt_card)
        prompt_l.setContentsMargins(30, 25, 30, 25)
        prompt_l.setSpacing(15)
        
        # Input + Button
        prompt_row = QHBoxLayout()
        prompt_row.setSpacing(12)
        self.input_ai_prompt = QLineEdit()
        self.input_ai_prompt.setPlaceholderText(MESSAGES.SETTINGS.PH_PROMPT)
        self.input_ai_prompt.setObjectName("ai_prompt_input")
        self.btn_generate_ai = QPushButton(MESSAGES.SETTINGS.BTN_GENERATE_AI)
        self.btn_generate_ai.setFixedWidth(180)
        self.btn_generate_ai.setObjectName("btn_generate_ai")
        prompt_row.addWidget(self.input_ai_prompt, 1)
        prompt_row.addWidget(self.btn_generate_ai)
        prompt_l.addLayout(prompt_row)
        
        l.addWidget(prompt_card)
        
        # ============================================================
        # CARD 6: GESTIÓN DE DATOS
        # ============================================================
        # Category Header (Outside card)
        data_header = QLabel("💾 " + MESSAGES.SETTINGS.LBL_DATA_MGMT.upper())
        data_header.setObjectName("settings_category_label")
        l.addWidget(data_header)
        
        # Card with settings only
        data_card = GlassCard()
        data_card.setProperty("depth", "settings")
        data_l = QVBoxLayout(data_card)
        data_l.setContentsMargins(30, 25, 30, 25)
        data_l.setSpacing(18)
        
        # Cloud Backup
        cloud_row = QHBoxLayout()
        cloud_row.setSpacing(15)
        cloud_info = QVBoxLayout()
        cloud_info.setSpacing(4)
        cloud_title = QLabel("☁️ " + MESSAGES.SETTINGS.LBL_CLOUD_BACKUP.upper())
        cloud_title.setObjectName("settings_label")
        cloud_desc = QLabel(MESSAGES.SETTINGS.DESC_CLOUD_BACKUP)
        cloud_desc.setObjectName("settings_desc")
        cloud_info.addWidget(cloud_title)
        cloud_info.addWidget(cloud_desc)
        cloud_buttons = QHBoxLayout()
        cloud_buttons.setSpacing(10)
        self.btn_backup = QPushButton(MESSAGES.SETTINGS.BTN_UPLOAD)
        self.btn_restore = QPushButton(MESSAGES.SETTINGS.BTN_DOWNLOAD)
        for b in [self.btn_backup, self.btn_restore]:
            b.setCursor(Qt.PointingHandCursor)
            b.setObjectName("btn_data_manage_cloud")
            b.setFixedWidth(120)
            cloud_buttons.addWidget(b)
        cloud_row.addLayout(cloud_info)
        cloud_row.addStretch()
        cloud_row.addLayout(cloud_buttons)
        data_l.addLayout(cloud_row)
        
        # Local Backup
        local_row = QHBoxLayout()
        local_row.setSpacing(15)
        local_info = QVBoxLayout()
        local_info.setSpacing(4)
        local_title = QLabel("📂 " + MESSAGES.SETTINGS.LBL_LOCAL_BACKUP.upper())
        local_title.setObjectName("settings_label")
        local_desc = QLabel(MESSAGES.SETTINGS.DESC_LOCAL_BACKUP)
        local_desc.setObjectName("settings_desc")
        local_info.addWidget(local_title)
        local_info.addWidget(local_desc)
        local_buttons = QHBoxLayout()
        local_buttons.setSpacing(10)
        self.btn_local_backup = QPushButton(MESSAGES.SETTINGS.BTN_BACKUP)
        self.btn_local_restore = QPushButton(MESSAGES.SETTINGS.BTN_RESTORE)
        for b in [self.btn_local_backup, self.btn_local_restore]:
            b.setCursor(Qt.PointingHandCursor)
            b.setObjectName("btn_data_manage_local")
            b.setFixedWidth(120)
            local_buttons.addWidget(b)
        local_row.addLayout(local_info)
        local_row.addStretch()
        local_row.addLayout(local_buttons)
        data_l.addLayout(local_row)
        
        # Zona de Peligro
        danger_row = QHBoxLayout()
        danger_row.setSpacing(15)
        danger_info = QVBoxLayout()
        danger_info.setSpacing(4)
        danger_title = QLabel("🔥 " + MESSAGES.SETTINGS.LBL_DANGER_ZONE.upper())
        danger_title.setObjectName("settings_label")
        danger_desc = QLabel(MESSAGES.SETTINGS.DESC_DANGER_ZONE)
        danger_desc.setObjectName("settings_desc")
        danger_info.addWidget(danger_title)
        danger_info.addWidget(danger_desc)
        self.btn_purge_private = QPushButton(MESSAGES.SETTINGS.BTN_PURGE_PRIVATE)
        self.btn_purge_private.setCursor(Qt.PointingHandCursor)
        self.btn_purge_private.setObjectName("btn_purge_private")
        self.btn_purge_private.setFixedWidth(200)
        danger_row.addLayout(danger_info)
        danger_row.addStretch()
        danger_row.addWidget(self.btn_purge_private)
        data_l.addLayout(danger_row)
        
        l.addWidget(data_card)
        
        l.addStretch()
        scroll.setWidget(page)
        main_v.addWidget(scroll)
        return container

    def retranslateUi(self):
        """NUCLEAR SYNC: Refreshes all UI components recursively."""
        try:
            # 1. Update the table (Vault view)
            self._load_table()
            
            # 2. Update navigation sidebar
            if hasattr(self, 'btn_nav_dashboard'): self.btn_nav_dashboard.setText("📊  " + MESSAGES.DASHBOARD.NAV_DASHBOARD.upper())
            if hasattr(self, 'btn_nav_vault'): self.btn_nav_vault.setText("📂  " + MESSAGES.DASHBOARD.NAV_VAULT.upper())
            if hasattr(self, 'btn_nav_activity'): self.btn_nav_activity.setText("📜  " + MESSAGES.DASHBOARD.NAV_ACTIVITY.upper())
            if hasattr(self, 'btn_nav_ai_side'): self.btn_nav_ai_side.setText("🤖  " + MESSAGES.DASHBOARD.NAV_AI.upper())
            if hasattr(self, 'btn_nav_users'): self.btn_nav_users.setText("👥  " + MESSAGES.DASHBOARD.NAV_USERS.upper())
            if hasattr(self, 'btn_nav_settings'): self.btn_nav_settings.setText("⚙️  " + MESSAGES.DASHBOARD.NAV_SETTINGS.upper())
            
            # [NUCLEAR REFRESH] Localized Combos
            if hasattr(self, 'combo_lang'):
                idx = self.combo_lang.currentIndex()
                self.combo_lang.clear()
                self.combo_lang.addItems(MESSAGES.LISTS.LANGUAGES)
                self.combo_lang.setCurrentIndex(idx)
                
            if hasattr(self, 'combo_theme'):
                idx = self.combo_theme.currentIndex()
                self.combo_theme.clear()
                self.combo_theme.addItems(MESSAGES.LISTS.THEMES)
                self.combo_theme.setCurrentIndex(idx)
                
            if hasattr(self, 'combo_lock_time'):
                idx = self.combo_lock_time.currentIndex()
                self.combo_lock_time.clear()
                self.combo_lock_time.addItems(MESSAGES.LISTS.LOCK_TIMES)
                self.combo_lock_time.setCurrentIndex(idx)
                
            if hasattr(self, 'combo_provider'):
                idx = self.combo_provider.currentIndex()
                self.combo_provider.clear()
                self.combo_provider.addItems(MESSAGES.LISTS.AI_PROVIDERS)
                self.combo_provider.setCurrentIndex(idx)
            
            # 3. Settings Page Titles
            if hasattr(self, 'settings_title'): self.settings_title.setText(MESSAGES.DASHBOARD.NAV_SETTINGS.upper())
            
            # 4. RECURSIVE CASCADING: Force all modular cards to refresh internally
            from PyQt5.QtWidgets import QWidget, QPushButton
            for child in self.findChildren(QWidget):
                # Modular Cards
                if hasattr(child, 'retranslateUi') and callable(child.retranslateUi) and child != self:
                    try:
                        child.retranslateUi()
                    except Exception as child_err:
                        logger.warning(f"Failed to retranslate child {child.__class__.__name__}: {child_err}")
                
                # Info Tiles titles
                elif hasattr(child, 'title_label') and hasattr(child, 'title_key'):
                    new_text = MESSAGES.INFO_TILES.get(child.title_key, child.title_key)
                    child.title_label.setText(new_text)
                
                # Quick Action Buttons
                elif isinstance(child, QPushButton) and hasattr(child, 'quick_key') and hasattr(child, 'quick_icon'):
                    new_text = MESSAGES.QUICK_ACTIONS.get(child.quick_key, child.quick_key)
                    child.setText(f"{child.quick_icon} {new_text}")

            # Force re-polish of the whole UI to ensure color/style changes propagate if any
            self.style().unpolish(self)
            self.style().polish(self)
            self.update()

            logger.info(f"RetranslateUI: Nuclear refresh complete (Lang={MESSAGES.LANG}).")
        except Exception as e:
            logger.error(f"RetranslateUI failed partially: {e}")
    def _start_clock(self): self.clock_timer = QTimer(self); self.clock_timer.timeout.connect(self._update_clock); self.clock_timer.start(1000)
    def _update_clock(self): pass
    def _password_strength_icon(self, pwd: str) -> str:
        score = self._score_password(pwd)
        return "🔒" if score >= 70 else "🔓"

    def _score_password(self, pwd: str) -> int:
        if not pwd or not isinstance(pwd, str): return 0
        if pwd == "[⚠️ Error de Llave]" or pwd == "[Bloqueado 🔑]": return 0
        s = 0
        if len(pwd) >= 8: s += 20
        if len(pwd) >= 12: s += 20
        if any(c.islower() for c in pwd): s += 20
        if any(c.isupper() for c in pwd): s += 20
        if any(c.isdigit() for c in pwd): s += 10
        if any(c in "!@#$%^&*()-_=+[]{}<>?/|\\;:.,~" for c in pwd): s += 10
        return s

    def _open_monitor_sessions(self):
        """Open the Active Sessions presence monitor"""
        dlg = SessionsDialog(self.sync_manager, current_username=self.current_username, parent=self)
        dlg.exec_()
