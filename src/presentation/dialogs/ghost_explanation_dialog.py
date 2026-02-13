from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QScrollArea, QWidget, QPushButton, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor, QFont, QPainter, QBrush
from src.presentation.theme_manager import ThemeManager
from src.domain.messages import MESSAGES

class GhostExplanationDialog(QDialog):
    def __init__(self, title, metrics_data, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        # [THEME FIX] Removed WA_TranslucentBackground to use solid theme colors
        # self.setAttribute(Qt.WA_TranslucentBackground)  # ❌ This forced transparency
        self.metrics_data = metrics_data 
        self.title_text = title
        self.setFixedSize(500, 600) # Size for the explanation card
        
        self.theme = ThemeManager()
        
        # [THEME FIX] Apply solid background color from theme BEFORE building UI
        colors = self.theme.get_theme_colors()
        self.setStyleSheet(f"QDialog {{ background-color: {colors['bg']}; }}")
        
        self.setup_ui()

    def setup_ui(self):
        colors = self.theme.get_theme_colors()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Main Container (The Ghost Glass)
        self.container = QFrame()
        self.container.setObjectName("ghost_container")
        
        # [THEME FIX] Use dynamic tokens for background and border
        qss = """
            QFrame#ghost_container {
                background-color: @bg_sec_95;
                border: 1px solid @border;
                border-radius: @border-radius-main;
            }
        """
        self.container.setStyleSheet(self.theme.apply_tokens(qss))
        
        # Shadow for depth
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(50)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.container.setGraphicsEffect(shadow)
        
        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(15)
        
        # Header
        header = QHBoxLayout()
        icon = QLabel("👻")
        icon.setStyleSheet("font-size: 24px;")
        
        lbl_title = QLabel(self.title_text)
        # Use primary color for title and theme font
        title_qss = f"color: @text; font-family: @font-family-main; font-size: 18px; font-weight: bold; letter-spacing: 0.5px;"
        lbl_title.setStyleSheet(self.theme.apply_tokens(title_qss))
        
        btn_close = QPushButton("✕")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setFixedSize(30, 30)
        
        close_qss = """
            QPushButton { color: @text_dim; background: transparent; border: none; font-weight: bold; font-size: 14px; }
            QPushButton:hover { color: @text; background: @ghost_white_15; border-radius: 15px; }
        """
        btn_close.setStyleSheet(self.theme.apply_tokens(close_qss))
        btn_close.clicked.connect(self.close)
        
        header.addWidget(icon)
        header.addWidget(lbl_title)
        header.addStretch()
        header.addWidget(btn_close)
        
        main_layout.addLayout(header)
        
        # Separator
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(self.theme.apply_tokens("background: @border;"))
        main_layout.addWidget(line)
        
        # Content Area (Scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 10, 10, 10)
        content_layout.setSpacing(15)
        
        # Dynamic Metric Rows
        for key, raw_value in self.metrics_data.items():
            self._add_metric_row(content_layout, key, raw_value)
            
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        # Footer hint
        lbl_hint = QLabel(MESSAGES.EXPLANATIONS.HINT_DISMISS)
        lbl_hint.setAlignment(Qt.AlignCenter)
        lbl_hint.setStyleSheet(self.theme.apply_tokens("color: @text_dim; font-size: 11px; font-style: italic; opacity: 0.7;"))
        main_layout.addWidget(lbl_hint)
        
        layout.addWidget(self.container)

    def _add_metric_row(self, layout, key, raw_value):
        row = QWidget()
        rl = QVBoxLayout(row)
        rl.setContentsMargins(0,0,0,0)
        rl.setSpacing(4)
        
        # Top line: Title + Value badge
        top = QHBoxLayout()
        lbl_k = QLabel(key)
        lbl_k.setStyleSheet(self.theme.apply_tokens("color: @text_dim; font-weight: 600; font-size: 13px;"))
        
        lbl_v = QLabel(raw_value)
        val_qss = "color: @primary; font-weight: bold; font-family: @font-family-main; font-size: 13px; background: @ghost_white_5; padding: 4px 8px; border-radius: 4px;"
        lbl_v.setStyleSheet(self.theme.apply_tokens(val_qss))
        
        top.addWidget(lbl_k)
        top.addStretch()
        top.addWidget(lbl_v)
        
        # Interpretation Logic
        interpretation, color_token = self._interpret_metric(key, raw_value)
        
        # [FIX] Enhanced Layout for Long Descriptions (System Status)
        # If the interpretation is the same as the raw_value (our pass-through case),
        # we hide the duplicate raw_value badge and show the description prominently with word wrap.
        if interpretation == str(raw_value):
            lbl_v.hide() # Hide the badge since it's just the text
            
            lbl_desc = QLabel(f"{interpretation}")
            lbl_desc.setWordWrap(True)
            # Increased line-height and font-size for better readability
            lbl_desc.setStyleSheet(self.theme.apply_tokens(f"color: {color_token}; font-size: 13px; line-height: 1.4; margin-top: 4px;"))
            
            rl.addLayout(top)
            rl.addWidget(lbl_desc)
        else:
            # Standard Short Metric Behavior
            lbl_desc = QLabel(f"➤ {interpretation}")
            lbl_desc.setWordWrap(True)
            lbl_desc.setStyleSheet(self.theme.apply_tokens(f"color: {color_token}; font-size: 12px; margin-left: 0px;"))
            
            rl.addLayout(top)
            rl.addWidget(lbl_desc)
        
        layout.addWidget(row)
        
        # Divider
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(self.theme.apply_tokens("background: @ghost_white_5;"))
        layout.addWidget(div)

    def _interpret_metric(self, key, value):
        # Default fallback
        interp = MESSAGES.EXPLANATIONS.INTERP_DEFAULT
        color_token = "@text_dim" # Grey
        
        # [FIX] Direct pass-through for System Status Explanations
        # If the key matches the specific System Status keys, we return the value (description) directly
        # and assign a neutral/info color.
        if key in [MESSAGES.EXPLANATIONS.SYS_SCORE, MESSAGES.EXPLANATIONS.SYS_STATUS, MESSAGES.EXPLANATIONS.SYS_LOAD]:
            return str(value), "@primary"

        key_lower = key.lower()
        val_lower = str(value).lower()
        
        # LOGIC: SYSTEM HEALTH (Score)
        if key == MESSAGES.EXPLANATIONS.SYS_HEALTH:
            try:
                score = int(''.join(filter(str.isdigit, str(value))))
                if score >= 80:
                    interp = MESSAGES.EXPLANATIONS.SYS_HEALTH_OPTIMAL
                    color_token = "@success"
                elif score >= 50:
                    interp = MESSAGES.EXPLANATIONS.SYS_HEALTH_MODERATE
                    color_token = "@warning"
                else:
                    interp = MESSAGES.EXPLANATIONS.SYS_HEALTH_CRITICAL
                    color_token = "@danger"
            except:
                interp = MESSAGES.EXPLANATIONS.SYS_HEALTH_MONITORING
        
        # LOGIC: AUTH INTEGRITY (MFA)
        elif key == MESSAGES.EXPLANATIONS.SYS_INTEGRITY:
            if "optimal" in val_lower or "high" in val_lower:
                interp = MESSAGES.EXPLANATIONS.AUTH_INTEGRITY_OPTIMAL
                color_token = "@success"
            elif "warning" in val_lower or "risk" in val_lower:
                interp = MESSAGES.EXPLANATIONS.AUTH_INTEGRITY_WARNING
                color_token = "@warning"
            else:
                interp = MESSAGES.EXPLANATIONS.AUTH_INTEGRITY_UNKNOWN

        # LOGIC: AUTH METRICS
        elif key == MESSAGES.EXPLANATIONS.AUTH_MFA:
             interp = MESSAGES.EXPLANATIONS.VAL_MFA_COVERAGE
             if "100" in val_lower: color_token = "@success"
             elif int(''.join(filter(str.isdigit, str(value) or "0"))) < 80: color_token = "@danger" 
             else: color_token = "@warning"
        elif key == MESSAGES.EXPLANATIONS.AUTH_ADMIN:
             interp = MESSAGES.EXPLANATIONS.VAL_ADMIN_SEC
             if "check" in val_lower or "low" in val_lower: color_token = "@danger"; interp += MESSAGES.EXPLANATIONS.VAL_ADMIN_SEC_ACTION
             else: color_token = "@success"
        elif key == MESSAGES.EXPLANATIONS.AUTH_SESSIONS:
             interp = MESSAGES.EXPLANATIONS.VAL_SESSIONS
             color_token = "@ai"
        elif key == MESSAGES.EXPLANATIONS.AUTH_POLICY:
             interp = MESSAGES.EXPLANATIONS.VAL_POLICY
             color_token = "@primary"
        elif key == MESSAGES.EXPLANATIONS.AUTH_FAILS:
             interp = MESSAGES.EXPLANATIONS.VAL_ATTEMPTS
             if int(''.join(filter(str.isdigit, str(value) or "0"))) > 5: color_token = "@danger"
             else: color_token = "@success"
        
        # LOGIC: PASSWORD HEALTH
        elif key == MESSAGES.EXPLANATIONS.HEALTH_WEAK:
             interp = MESSAGES.EXPLANATIONS.VAL_WEAK
             if int(value) > 0: color_token = "@danger"
             else: color_token = "@success"
        elif key == MESSAGES.EXPLANATIONS.HEALTH_REUSED:
             interp = MESSAGES.EXPLANATIONS.VAL_REUSED
             if int(value) > 0: color_token = "@warning"
             else: color_token = "@success"
        elif key == MESSAGES.EXPLANATIONS.HEALTH_EXPIRED:
             interp = MESSAGES.EXPLANATIONS.VAL_EXPIRED
             color_token = "@text_dim"
        elif key == MESSAGES.EXPLANATIONS.HEALTH_SCORE:
             interp = MESSAGES.EXPLANATIONS.VAL_SCORE
             color_token = "@primary"
             
        # LOGIC: SECURITY WATCH / THREATS
        elif key == MESSAGES.EXPLANATIONS.WATCH_STATUS:
             interp = MESSAGES.EXPLANATIONS.VAL_THREAT
             if "secure" in val_lower or "seguro" in val_lower: color_token = "@success"
             else: color_token = "@danger"
        elif key == MESSAGES.EXPLANATIONS.WATCH_ACCESS:
             interp = MESSAGES.EXPLANATIONS.VAL_ACCESS
             color_token = "@secondary"
        elif key == MESSAGES.EXPLANATIONS.WATCH_POLICY:
             interp = MESSAGES.EXPLANATIONS.VAL_ROTATION
             color_token = "@text_dim" # More neutral
        elif key == MESSAGES.EXPLANATIONS.WATCH_RISK:
             interp = MESSAGES.EXPLANATIONS.VAL_RISK_ASSESS
             color_token = "@warning"
 
        # LOGIC: AI GUARDIAN
        elif key == MESSAGES.EXPLANATIONS.AI_STATUS:
             interp = MESSAGES.EXPLANATIONS.VAL_AI_ACTIVE
             color_token = "@success"
        elif key == MESSAGES.EXPLANATIONS.AI_RISKS:
             count = int(''.join(filter(str.isdigit, str(value) or "0")))
             interp = MESSAGES.EXPLANATIONS.VAL_AI_RISKS
             if count > 0: color_token = "@warning"; interp += MESSAGES.EXPLANATIONS.VAL_AI_RISKS_ACTION
             else: color_token = "@success"
        elif key == MESSAGES.EXPLANATIONS.AI_LATENCY:
             interp = MESSAGES.EXPLANATIONS.VAL_AI_LATENCY
             color_token = "@text_dim"
        elif key == MESSAGES.EXPLANATIONS.AI_MODEL:
             interp = MESSAGES.EXPLANATIONS.VAL_AI_MODEL
             color_token = "@ai"
        
        # DEEP DIVE: RADAR / SONAR
        elif key == MESSAGES.EXPLANATIONS.AI_SECTOR_HEAD:
             interp = MESSAGES.EXPLANATIONS.INTERP_RADAR
             color_token = "@secondary"
 
        # DEEP DIVE: SONAR SECTORS
        elif MESSAGES.EXPLANATIONS.AI_SECTOR in key:
            k_low = key.lower()
            if "strength" in k_low or "maestra" in k_low:
                interp = MESSAGES.EXPLANATIONS.SECTOR_STRENGTH
            elif "auth" in k_low or "identidad" in k_low:
                interp = MESSAGES.EXPLANATIONS.SECTOR_AUTH
            elif "health" in k_low or "salud" in k_low:
                interp = MESSAGES.EXPLANATIONS.SECTOR_HEALTH
            elif "rotation" in k_low or "rotación" in k_low:
                interp = MESSAGES.EXPLANATIONS.SECTOR_ROTATION
            elif "intel" in k_low:
                interp = MESSAGES.EXPLANATIONS.SECTOR_INTEL
            elif "sync" in k_low or "nube" in k_low:
                interp = MESSAGES.EXPLANATIONS.SECTOR_SYNC
            elif "records" in k_low or "digital" in k_low:
                interp = MESSAGES.EXPLANATIONS.SECTOR_RECORDS
            elif "risk" in k_low or "riesgo" in k_low:
                interp = MESSAGES.EXPLANATIONS.SECTOR_RISK
            color_token = "@warning"
 
        # LOGIC: ACTIVITY
        elif key == MESSAGES.EXPLANATIONS.ACT_SOURCE:
             interp = MESSAGES.EXPLANATIONS.VAL_ACT_SOURCE
             color_token = "@primary"
        elif key == MESSAGES.EXPLANATIONS.ACT_FREQ:
             interp = MESSAGES.EXPLANATIONS.VAL_ACT_FREQ
             color_token = "@warning"
        elif key == MESSAGES.EXPLANATIONS.ACT_STATUS:
             interp = MESSAGES.EXPLANATIONS.VAL_ACT_STATUS
             color_token = "@success"
 
        # LOGIC: ENCRYPTION / STORAGE / PROTOCOL (System card breakdown)
        elif key == MESSAGES.EXPLANATIONS.SYS_ENCRYPTION:
            interp = MESSAGES.EXPLANATIONS.VAL_ENCRYPTION
            color_token = "@primary"
        elif key == MESSAGES.EXPLANATIONS.SYS_STORAGE:
            interp = MESSAGES.EXPLANATIONS.VAL_STORAGE
            color_token = "@text_dim"
        elif key == MESSAGES.EXPLANATIONS.SYS_RISK:
            interp = MESSAGES.EXPLANATIONS.VAL_RISK_ASSESS
            if "high" in val_lower or "alto" in val_lower: color_token = "@danger"
            else: color_token = "@success"
        elif key == MESSAGES.EXPLANATIONS.SYS_PROTOCOL:
            interp = MESSAGES.EXPLANATIONS.VAL_PROTOCOL
            color_token = "@ai"
            
        return interp, color_token

    def mouseDoubleClickEvent(self, event):
        self.close()
