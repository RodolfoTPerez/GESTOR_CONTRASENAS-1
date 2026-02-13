from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


class VaultIdentityBanner(QWidget):
    """
    HUD Identity Banner - Premium Cyber-Ops Edition.
    Glassmorphism, tactical typography, and neon detailing.
    """
    def __init__(self, vault_name="VULTRAX CORE", show_badge=True, parent=None):
        super().__init__(parent)
        self.setFixedHeight(85) # Increased height for more presence
        self.setObjectName("IdentityHUD")

        # Container for Glass Effect
        self.container = QFrame(self)
        self.container.setObjectName("hud_container")
        self.container.setGeometry(0, 0, 0, 0) # Managed by resizeEvent or Layout
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.setSpacing(10)
        
        # --- NEW GLASS WRAPPER ---
        self.glass_box = QFrame()
        self.glass_box.setObjectName("hud_glass_box")
        layout = QVBoxLayout(self.glass_box)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)

        # 1. ICON + TITLE ROW
        header_row = QHBoxLayout()
        self.lbl_v_icon = QLabel("🛡️")
        self.lbl_v_icon.setObjectName("hud_v_icon")
        self.lbl_v_icon.setStyleSheet("font-size: 20px;")
        
        self.lbl_v_name = QLabel(vault_name.upper())
        self.lbl_v_name.setObjectName("hud_v_name")
        self.lbl_v_name.setStyleSheet("font-size: 16px; font-weight: 900;")
        
        header_row.addWidget(self.lbl_v_icon)
        header_row.addWidget(self.lbl_v_name)
        header_row.addStretch()
        layout.addLayout(header_row)

        # 2. STATUS HUD (Telemetría)
        self.hud_right_layout = QHBoxLayout()
        self.hud_right_layout.setContentsMargins(0, 0, 0, 0)
        self.hud_right_layout.setSpacing(10)
        self.hud_right_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        layout.addLayout(self.hud_right_layout)

        # 3. STATS DECORATION (Subtle HUD details)
        # self.hud_deco = QLabel("NETWORK: STABLE | NODE: MASTER") # Removed old label to clean space
        # self.hud_deco.setObjectName("hud_metadata")
        # layout.addWidget(self.hud_deco)

        # 4. SECURITY BADGE (Removed from banner, moving to Sidebar as requested)
        if show_badge:
            pass # We will handle badge creation in DashboardUI for the sidebar

        main_layout.addWidget(self.glass_box)

        # Initialize ThemeManager and apply initial theme
        from src.presentation.theme_manager import ThemeManager
        self.tm = ThemeManager()
        self.refresh_theme()

    def refresh_theme(self):
        style = self.tm.apply_tokens("""
            #hud_glass_box {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 @ghost_primary_15, 
                            stop:1 @ghost_bg_dark);
                border: @border-width-main solid @ghost_border;
                border-radius: @border-radius-main;
            }
            #hud_v_icon {
                font-size: 28px;
            }
            #hud_v_type {
                color: @ghost_secondary_75;
                font-family: @font-family-main;
                font-size: 9px;
                font-weight: 800;
                letter-spacing: 2px;
            }
            #hud_v_name {
                color: @text;
                font-family: @font-family-main;
                font-size: 22px;
                font-weight: 900;
                letter-spacing: 3px;
            }
            #hud_metadata {
                color: @ghost_text_30;
                font-family: 'Consolas';
                font-size: 10px;
                letter-spacing: 1px;
                margin-right: 20px;
            }
            #hud_v_badge {
                background: @ghost_success_10;
                border: 1px solid @ghost_success_30;
                border-radius: 6px;
            }
            #hud_v_badge_status {
                color: @success;
                font-family: 'Consolas';
                font-size: 11px;
                font-weight: bold;
            }
            #hud_v_badge_label {
                color: @ghost_success_65;
                font-family: 'Consolas';
                font-size: 9px;
            }
        """)
        self.setStyleSheet(style)
    
    def set_vault_name(self, name):
        """Update the vault name dynamically"""
        self.lbl_v_name.setText(name.upper())
