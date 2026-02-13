from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QComboBox, 
    QPushButton, QLineEdit, QTableWidget, QWidget, QSlider, 
    QCheckBox, QRadioButton, QButtonGroup, QScrollArea, QGridLayout, 
    QLayout, QStackedWidget, QGraphicsDropShadowEffect, QHeaderView
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QDateTime, QTimer, QSize
from PyQt5.QtGui import QPixmap, QIcon, QFont, QColor, QLinearGradient
from src.domain.messages import MESSAGES
from src.presentation.widgets.glass_card import GlassCard
from src.presentation.widgets.circular_gauge import CircularGauge

class DashboardUI:
    def _build_ui(self):
        # 1. DESIGN SYSTEM (Apple-Military SaaS)
        # 1. DESIGN SYSTEM (Glass-Cyber 2026)
        self.setStyleSheet("""
            /* --- BASE IDENTITY --- */
            QWidget { 
                background-color: #0F172A; /* Midnight Blue Deep */
                color: #e2e8f0; 
                font-family: 'Inter', 'Segoe UI', sans-serif; 
            }
            
            /* --- SIDEBAR (Glass Column) --- */
            QFrame#sidebar { 
                background-color: rgba(15, 23, 42, 0.95); 
                border-right: 1px solid rgba(6, 182, 212, 0.15); /* Cyan separator */
            }
            
            /* --- NAVIGATION --- */
            QPushButton#nav_btn {
                text-align: left; 
                padding: 14px 24px; 
                border: 1px solid transparent; 
                border-radius: 16px;
                font-size: 13px; 
                font-weight: 600; 
                color: #94a3b8; 
                margin: 6px 16px; 
                background: transparent;
            }
            QPushButton#nav_btn:hover { 
                background-color: rgba(30, 41, 59, 0.5); 
                color: #f8fafc; 
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
            QPushButton#nav_btn:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(6, 182, 212, 0.2), stop:1 rgba(6, 182, 212, 0.05));
                color: #22d3ee; /* Cyan Electric */
                border: 1px solid rgba(6, 182, 212, 0.3);
                border-left: 3px solid #06b6d4;
            }
            
            /* --- TOPBAR & SEARCH --- */
            QFrame#topbar { 
                background-color: rgba(15, 23, 42, 0.85); 
                border-bottom: 1px solid rgba(255, 255, 255, 0.03); 
            }
            QLineEdit#search_bar {
                background-color: rgba(30, 41, 59, 0.4); 
                border: 1px solid rgba(255, 255, 255, 0.08); 
                border-radius: 14px;
                padding: 12px 20px; 
                color: #f1f5f9; 
                font-size: 13px;
                selection-background-color: #06b6d4;
            }
            QLineEdit#search_bar:focus {
                border: 1px solid #06b6d4;
                background-color: rgba(6, 182, 212, 0.05);
            }
            
            /* --- GLASS CARDS (The core aesthetic) --- */
            QFrame#glass_card { 
                background-color: rgba(30, 41, 59, 0.35); /* Deep translucent */
                border: 1px solid rgba(255, 255, 255, 0.06); 
                border-radius: 24px; 
            }
            QFrame#glass_card:hover {
                border: 1px solid rgba(255, 255, 255, 0.12);
                background-color: rgba(30, 41, 59, 0.5); 
            }
            
            /* --- ACTIONS --- */
            QPushButton#panic_btn {
                background-color: rgba(127, 29, 29, 0.2); 
                color: #f87171; 
                border: 1px solid #ef4444;
                border-radius: 12px; 
                padding: 10px 24px; 
                font-weight: 800; 
                font-size: 11px;
                text-transform: uppercase; 
                letter-spacing: 2px;
            }
            QPushButton#panic_btn:hover { 
                background-color: #ef4444; 
                color: white; 
            }

            /* --- DATA TABLES --- */
            QTableWidget { 
                background: transparent; 
                border: none; 
                gridline-color: transparent; 
                alternate-background-color: rgba(255, 255, 255, 0.02); 
                font-size: 13px; 
                outline: none;
                padding-bottom: 20px;
                selection-background-color: rgba(6, 182, 212, 0.1);
                selection-color: white;
            }
            QTableWidget::item { 
                border-bottom: 1px solid rgba(255, 255, 255, 0.04); 
                padding: 12px; 
            }
            QTableWidget::item:selected {
                border-left: 2px solid #06b6d4;
            }
            
            QHeaderView::section { 
                background-color: rgba(15, 23, 42, 0.9); 
                color: #06b6d4; /* Cyan Headers */
                padding: 14px; 
                border: none; 
                font-weight: 900; 
                font-size: 10px; 
                text-transform: uppercase; 
                letter-spacing: 1.5px;
            }

            /* --- SCROLLBARS (Invisible but functional) --- */
            QScrollBar:horizontal { height: 8px; background: #0F172A; }
            QScrollBar:vertical { 
                width: 8px; 
                background: #0F172A; 
                border: none;
            }
            QScrollBar::handle { 
                background: #334155; 
                border-radius: 4px; 
            }
            QScrollBar::handle:hover { background: #475569; }
            QScrollBar::add-line, QScrollBar::sub-line { border: none; background: none; }
        """)

        main_layout = QHBoxLayout(self); main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)

        # ================= SIDEBAR =================
        self.sidebar = QFrame(); self.sidebar.setObjectName("sidebar"); self.sidebar.setFixedWidth(260)
        sidebar_layout = QVBoxLayout(self.sidebar); sidebar_layout.setContentsMargins(0, 40, 0, 40)
        
        lbl_logo = QLabel("🛡️ PASSGUARDIAN"); lbl_logo.setAlignment(Qt.AlignCenter)
        lbl_logo.setStyleSheet("font-size: 16px; font-weight: 900; color: white; letter-spacing: 6px; margin-bottom: 40px;")
        sidebar_layout.addWidget(lbl_logo)
        
        self.nav_group = QButtonGroup(self); self.nav_group.setExclusive(True)
        def add_nav(lbl, ic, idx):
            btn = QPushButton(f"  {ic}   {lbl}"); btn.setObjectName("nav_btn"); btn.setCheckable(True)
            btn.setFixedHeight(54); btn.clicked.connect(lambda: self.main_stack.setCurrentIndex(idx))
            self.nav_group.addButton(btn); sidebar_layout.addWidget(btn); return btn

        self.btn_nav_dashboard = add_nav("Dashboard", "📊", 0)
        self.btn_nav_vault = add_nav("Bóveda (Vault)", "🔑", 1) # Full-view mirror
        self.btn_nav_ai_side = add_nav("Guardian AI", "🧠", 2)
        self.btn_nav_activity = add_nav("Historial", "📜", 3)
        self.btn_nav_users = add_nav("Admin Panel", "👮", 4)
        sidebar_layout.addStretch()
        self.btn_nav_settings = add_nav("Configuración", "⚙️", 5)
        
        u_card = QFrame(); u_layout = QHBoxLayout(u_card); self.lbl_user_info = QLabel(f"👤 {self.current_username}")
        self.btn_logout = QPushButton("🚪"); self.btn_logout.setFixedSize(30, 30); self.btn_logout.setStyleSheet("background: #ef4444; border-radius: 8px;")
        self.btn_logout.clicked.connect(self.logout)
        u_layout.addWidget(self.lbl_user_info); u_layout.addStretch(); u_layout.addWidget(self.btn_logout)
        sidebar_layout.addWidget(u_card)
        main_layout.addWidget(self.sidebar)

        # ================= MAIN CONTENT =================
        content_box = QWidget(); content_layout = QVBoxLayout(content_box); content_layout.setContentsMargins(0,0,0,0); content_layout.setSpacing(0)
        
        # TOPBAR
        self.topbar = QFrame(); self.topbar.setObjectName("topbar"); self.topbar.setFixedHeight(85)
        top_l = QHBoxLayout(self.topbar); top_l.setContentsMargins(40, 0, 40, 0); top_l.setSpacing(15)
        self.search_input = QLineEdit(); self.search_input.setObjectName("search_bar"); self.search_input.setPlaceholderText("Buscador global..."); self.search_input.setFixedWidth(400)
        top_l.addWidget(self.search_input); top_l.addStretch()
        
        # INDICADORES DE INFRAESTRUCTURA (SaaS Moderno)
        status_style = """
            QLabel {
                font-weight: 900; 
                font-size: 9px; 
                padding: 6px 12px; 
                border-radius: 6px; 
                background: rgba(15, 23, 42, 0.8); 
                border: 1px solid rgba(255, 255, 255, 0.05);
                color: #94a3b8;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
        """
        
        self.status_internet = QLabel("🌐 INTERNET")
        self.status_internet.setObjectName("status_badge")
        self.status_internet.setStyleSheet(status_style)
        
        self.status_supabase = QLabel("☁️ SUPABASE")
        self.status_supabase.setObjectName("status_badge")
        self.status_supabase.setStyleSheet(status_style)
        
        self.status_sqlite = QLabel("📂 SQLITE")
        self.status_sqlite.setObjectName("status_badge")
        self.status_sqlite.setStyleSheet(status_style)
        
        self.lbl_countdown = QLabel("⌛ 10:00")
        self.lbl_countdown.setObjectName("status_badge")
        self.lbl_countdown.setStyleSheet(status_style + "background: rgba(245, 158, 11, 0.1); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); min-width: 80px;")
        
        top_l.addWidget(self.status_internet)
        top_l.addWidget(self.status_supabase)
        top_l.addWidget(self.status_sqlite)
        top_l.addWidget(self.lbl_countdown)
        
        self.btn_panic = QPushButton("PANIC SWITCH"); self.btn_panic.setObjectName("panic_btn"); top_l.addWidget(self.btn_panic)
        content_layout.addWidget(self.topbar)

        # STACK
        self.main_stack = QStackedWidget()
        self.view_dashboard = self._module_dashboard() # Hub Principal
        self.view_vault = self._module_vault()         # Copia de tabla dedicada
        self.view_ai = self._module_ai()
        self.view_activity = self._module_activity()
        self.view_users = self._module_admin()
        self.view_settings = self._module_settings()   # Aquí está todo lo técnico (Keys, Generador, Passwd)
        
        for v in [self.view_dashboard, self.view_vault, self.view_ai, self.view_activity, self.view_users, self.view_settings]: self.main_stack.addWidget(v)
        content_layout.addWidget(self.main_stack); main_layout.addWidget(content_box)
        
        self.btn_nav_dashboard.setChecked(True); self.main_stack.setCurrentIndex(0)
        
        # Compatibility Holders (Solo los que faltan)
        self.status_sync = QLabel(); self.status_datetime = QLabel()

    def _module_dashboard(self):
        """
        DASHBOARD HUB (Bento Style 2026):
        - Top Left: Health Center (Gauge)
        - Top Right: Pulse Stats (Vertical Cards)
        - Middle: Live Vault (Table)
        - Bottom: Audit Stream
        """
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 30, 40, 40)
        layout.setSpacing(25)
        
        # --- BENTO TOP SECTION (Health + Stats) ---
        top_grid = QGridLayout()
        top_grid.setSpacing(20)
        
        # Box 1: Health Center (Large Square)
        health_card = GlassCard()
        health_card.setFixedSize(260, 260)
        hl = QVBoxLayout(health_card)
        hl.setAlignment(Qt.AlignCenter)
        
        self.gauge = CircularGauge()
        self.gauge.setFixedSize(140, 140)
        hl.addWidget(self.gauge)
        
        lbl_h = QLabel("SALUD DE BÓVEDA")
        lbl_h.setStyleSheet("font-size: 11px; font-weight: 900; color: #94a3b8; letter-spacing: 2px; margin-top: 15px;")
        hl.addWidget(lbl_h, alignment=Qt.AlignCenter)
        
        top_grid.addWidget(health_card, 0, 0)
        
        # Box 2: Pulse Stats (2x2 Grid inside the top area or a horizontal strip?) 
        # Making it a horizontal grid to fill the width next to the gauge
        stats_container = QWidget()
        sl = QHBoxLayout(stats_container); sl.setContentsMargins(0,0,0,0); sl.setSpacing(20)
        
        def create_bento_stat(title, val, icon, color):
            c = GlassCard()
            c.setObjectName("glass_card")
            c.setFixedHeight(260) # Match height of gauge card
            cl = QVBoxLayout(c)
            cl.setContentsMargins(20,20,20,20)
            
            # Icon Top Left
            ic_lbs = QLabel(icon); ic_lbs.setStyleSheet(f"font-size: 24px; color: {color};")
            cl.addWidget(ic_lbs)
            cl.addStretch()
            
            # Value Big
            v_lbl = QLabel(val); v_lbl.setStyleSheet("font-size: 42px; font-weight: 900; color: white;")
            cl.addWidget(v_lbl)
            
            # Title Bottom
            t_lbl = QLabel(title); t_lbl.setStyleSheet("font-size: 11px; font-weight: 800; color: #64748b; letter-spacing: 1px;")
            cl.addWidget(t_lbl)
            return c, v_lbl
            
        self.card_total, self.stat_total_val = create_bento_stat("TOTAL KEYS", "0", "🔑", "#06b6d4")
        self.card_weak, self.stat_weak_val = create_bento_stat("RIESGOS", "0", "🛡️", "#ef4444")
        self.card_sessions, self.stat_sess_val = create_bento_stat("SESIONES", "0", "💻", "#10b981")
        
        self.stat_total = self.card_total; self.stat_weak = self.card_weak; self.stat_devices = self.card_sessions
        
        sl.addWidget(self.card_total)
        sl.addWidget(self.card_weak)
        sl.addWidget(self.card_sessions)
        
        top_grid.addWidget(stats_container, 0, 1)
        
        # Adjust column stretch to make stats take up remaining space
        top_grid.setColumnStretch(1, 1)
        layout.addLayout(top_grid)
        
        # --- MIDDLE SECTION: LIVE VAULT ---
        # Header for Table
        mid_head = QHBoxLayout()
        mid_head.addWidget(QLabel("BÓVEDA PRINCIPAL", styleSheet="font-weight: 900; font-size: 11px; color: #06b6d4; letter-spacing: 2px;"))
        mid_head.addStretch()
        
        self.btn_add = QPushButton(" ➕  AGREGAR "); self.btn_sync = QPushButton(" 🔄  SYNC ")
        for b in [self.btn_add, self.btn_sync]: 
            b.setStyleSheet("background: rgba(6, 182, 212, 0.1); color: #22d3ee; border: 1px solid #06b6d4; padding: 8px 16px; border-radius: 6px; font-weight: 700; font-size: 10px;")
            mid_head.addWidget(b)
            
        self.btn_delete = QPushButton(" 🗑️ "); 
        self.btn_delete.setStyleSheet("background: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid #ef4444; padding: 8px 16px; border-radius: 6px; font-weight: 700;")
        mid_head.addWidget(self.btn_delete)
        
        layout.addLayout(mid_head)
        
        t_card = GlassCard()
        t_layout = QVBoxLayout(t_card); t_layout.setContentsMargins(1, 1, 1, 1)
        
        # TABLA REFINADA (DISEÑO PREMIUM 2026 - BALANCEADO)
        self.table = QTableWidget(0, 7)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setHorizontalHeaderLabels(["SEL", "LVL", "SYNC", "SERVICIO", "USUARIO", "CLAVE", "ESTADO"])
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #0f172a;
                alternate-background-color: rgba(30, 41, 59, 0.4);
                gridline-color: transparent;
                border: none;
                color: #f1f5f9;
                font-size: 13px;
                selection-background-color: rgba(6, 182, 212, 0.15);
                selection-color: #22d3ee;
                outline: none;
            }
            QTableWidget::item { 
                padding: 12px; 
                border: 0px;
                border-bottom: 1px solid rgba(255,255,255,0.03);
            }
            QHeaderView::section {
                background-color: #0f172a;
                color: #64748b;
                padding: 15px;
                border: none;
                border-bottom: 2px solid rgba(6, 182, 212, 0.2);
                font-weight: 800;
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 1.5px;
            }
        """)
        
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Fixed)
        
        # BLOQUEO TOTAL DE ANCHOS (Sincronización Garantizada)
        self.table.setColumnWidth(0, 45)  # SEL
        self.table.setColumnWidth(1, 45)  # LVL
        self.table.setColumnWidth(2, 45)  # SYNC
        self.table.setColumnWidth(3, 200) # SERVICIO
        self.table.setColumnWidth(4, 200) # USUARIO
        self.table.setColumnWidth(5, 450) # CLAVE (Espacio masivo para secretos)
        self.table.setColumnWidth(6, 65)  # ESTADO
        
        t_layout.addWidget(self.table)
        
        # --- PANEL LATERAL (Invisible por defecto hasta clic) ---
        self.side_panel_dashboard = QWidget()
        self.side_panel_dashboard.setFixedWidth(0)
        self.side_panel_dashboard.setObjectName("side_detail_panel")
        
        table_with_panel = QHBoxLayout()
        table_with_panel.addWidget(t_card)
        table_with_panel.addWidget(self.side_panel_dashboard)
        
        layout.addLayout(table_with_panel)

        # --- BARRA FLOTANTE (Solo aparece al seleccionar) ---
        self.float_bar_dashboard = QFrame()
        self.float_bar_dashboard.setFixedHeight(0) # Oculta
        self.float_bar_dashboard.setStyleSheet("background: rgba(15, 23, 42, 0.9); border: 1px solid #06b6d4; border-radius: 15px;")
        layout.addWidget(self.float_bar_dashboard)
        
        # --- BOTTOM SECTION: AUDIT STREAM (Compact) ---
        h_card = GlassCard()
        h_card.setFixedHeight(140)
        hl = QHBoxLayout(h_card); hl.setContentsMargins(20, 10, 20, 10); hl.setSpacing(20)
        
        hl.addWidget(QLabel("LIVE\nLOGS", styleSheet="font-family: 'Courier New'; font-weight: 900; color: #64748b; font-size: 10px;"))
        
        self.table_mini_audit = QTableWidget(0, 3)
        self.table_mini_audit.horizontalHeader().setVisible(False)
        self.table_mini_audit.verticalHeader().setVisible(False)
        self.table_mini_audit.setShowGrid(False)
        self.table_mini_audit.setStyleSheet("background: transparent; font-size: 11px; font-family: 'Consolas', monospace; color: #94a3b8;")
        # Fix columns for compact view
        self.table_mini_audit.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        hl.addWidget(self.table_mini_audit)
        
        layout.addWidget(h_card)
        
        return page

    def _module_vault(self):
        """Módulo Bóveda: Vista completa y dedicada de secretos."""
        page = QWidget(); l = QVBoxLayout(page); l.setContentsMargins(40, 20, 40, 40); l.setSpacing(20)
        
        header = QHBoxLayout(); title = QLabel("Bóveda de Seguridad"); title.setStyleSheet("font-size: 26px; font-weight: 900; color: white;")
        header.addWidget(title); header.addStretch()
        
        # --- NUEVOS BOTONES DE ACCIÓN (Import/Export) ---
        self.btn_import = QPushButton("  📥 IMPORTAR  ")
        self.btn_export = QPushButton("  📤 EXPORTAR  ")
        self.btn_import.setCursor(Qt.PointingHandCursor)
        self.btn_export.setCursor(Qt.PointingHandCursor)
        
        # Estilo "Glass Action"
        action_style = """
            QPushButton {
                background: rgba(30, 41, 59, 0.6); 
                color: #cbd5e1; 
                border: 1px solid rgba(255,255,255,0.1); 
                border-radius: 8px; 
                padding: 10px 15px; 
                font-weight: 700; font-size: 11px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1); 
                color: white; border: 1px solid rgba(255,255,255,0.3);
            }
        """
        self.btn_import.setStyleSheet(action_style)
        self.btn_export.setStyleSheet(action_style)
        
        header.addWidget(self.btn_import)
        header.addWidget(self.btn_export)
        header.addSpacing(10)
        
        self.btn_add_vault = QPushButton("  ➕  AGREGAR NUEVO SERVICIO  ")
        self.btn_add_vault.setCursor(Qt.PointingHandCursor)
        self.btn_add_vault.setStyleSheet("""
            QPushButton {
                background: rgba(6, 182, 212, 0.1); 
                color: #22d3ee; 
                border: 1px solid #06b6d4; 
                padding: 15px 30px; 
                border-radius: 12px; 
                font-weight: 800; 
                font-size: 11px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: rgba(6, 182, 212, 0.2);
                border: 1px solid #22d3ee;
            }
        """)

        header.addWidget(self.btn_add_vault); l.addLayout(header)
        
        t_card = GlassCard(); t_card.setObjectName("glass_card"); tl = QVBoxLayout(t_card); tl.setContentsMargins(15, 15, 15, 25)
        
        # TABLA BOVEDA (SINCRONIZADA CON DASHBOARD)
        self.table_vault = QTableWidget(0, 7)
        self.table_vault.setAlternatingRowColors(True)
        self.table_vault.verticalHeader().setVisible(False)
        self.table_vault.setShowGrid(False)
        self.table_vault.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_vault.setHorizontalHeaderLabels(["SEL", "LVL", "SYNC", "SERVICIO", "USUARIO", "CLAVE", "ESTADO"])
        
        # Estilo unificado
        self.table_vault.setStyleSheet(self.table.styleSheet())
        
        hhv = self.table_vault.horizontalHeader()
        hhv.setSectionResizeMode(QHeaderView.Fixed)
        
        self.table_vault.setColumnWidth(0, 45)
        self.table_vault.setColumnWidth(1, 45)
        self.table_vault.setColumnWidth(2, 45)
        self.table_vault.setColumnWidth(3, 200)
        self.table_vault.setColumnWidth(4, 200)
        self.table_vault.setColumnWidth(5, 450)
        self.table_vault.setColumnWidth(6, 65)
        
        tl.addWidget(self.table_vault)
        
        # --- PANEL LATERAL (Vault) ---
        self.side_panel_vault = QWidget()
        self.side_panel_vault.setFixedWidth(0)
        self.side_panel_vault.setObjectName("side_detail_panel_vault")
        
        table_vault_with_panel = QHBoxLayout()
        table_vault_with_panel.addWidget(t_card)
        table_vault_with_panel.addWidget(self.side_panel_vault)
        
        l.addLayout(table_vault_with_panel)

        # --- BARRA FLOTANTE (Vault) ---
        self.float_bar_vault = QFrame()
        self.float_bar_vault.setFixedHeight(0)
        self.float_bar_vault.setStyleSheet("background: rgba(15, 23, 42, 0.9); border: 1px solid #06b6d4; border-radius: 15px;")
        l.addWidget(self.float_bar_vault)
        
        v_actions = QHBoxLayout(); self.btn_sync_vault = QPushButton(" 🔄 SINCRONIZAR TODO "); self.btn_sync_vault.setFixedWidth(250)
        self.btn_sync_vault.setCursor(Qt.PointingHandCursor)
        self.btn_sync_vault.setStyleSheet("background: rgba(6, 182, 212, 0.1); color: #22d3ee; border: 1px solid #06b6d4; border-radius: 10px; padding: 12px; font-weight: 800;")
        v_actions.addStretch(); v_actions.addWidget(self.btn_sync_vault); l.addLayout(v_actions)
        return page

    def _module_ai(self):
        """
        AI NEURAL HUB (Bento Style 2026):
        - Left: Neural Engine Status (Visual)
        - Right: Operations Command Center
        """
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)
        
        # --- LEFT: NEURAL CORE VISUAL ---
        core_card = GlassCard()
        cl = QVBoxLayout(core_card); cl.setAlignment(Qt.AlignCenter); cl.setSpacing(10)
        
        # Simulated Brain Visual
        core_lbl = QLabel("🧠")
        core_lbl.setStyleSheet("font-size: 80px; margin-bottom: 20px;")
        cl.addWidget(core_lbl)
        
        cl.addWidget(QLabel("GUARDIAN NEURAL ENGINE", styleSheet="font-weight: 900; color: #a855f7; font-size: 14px; letter-spacing: 2px;"))
        cl.addWidget(QLabel("Monitoring heuristic patterns...", styleSheet="color: #64748b; font-size: 11px; font-family: 'Consolas';"))
        
        layout.addWidget(core_card, 1) # Stretch 1
        
        # --- RIGHT: OPERATIONS CENTER ---
        ops_card = GlassCard()
        ol = QVBoxLayout(ops_card); ol.setContentsMargins(40, 40, 40, 40); ol.setSpacing(20)
        
        ol.addWidget(QLabel("AI OPERATIONS", styleSheet="color: #c084fc; font-weight: 900; font-size: 12px; letter-spacing: 1px;"))
        ol.addWidget(QLabel("Execute deep scan analysis across all vault entries to detect weak patterns and duplicates.", styleSheet="color: #94a3b8; font-size: 13px; margin-bottom: 20px;"))
        
        self.btn_ai_invoke = QPushButton("  ⚡  INICIAR ESCANEO PROFUNDO  ")
        self.btn_ai_invoke.setFixedHeight(60)
        self.btn_ai_invoke.setCursor(Qt.PointingHandCursor)
        self.btn_ai_invoke.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #a855f7);
                color: white;
                border: none;
                border-radius: 12px;
                font-weight: 900;
                font-size: 14px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6d28d9, stop:1 #9333ea);
                border: 2px solid rgba(255,255,255,0.2);
            }
        """)
        
        ol.addWidget(self.btn_ai_invoke)
        ol.addStretch()
        
        # Mini Console
        console = QLabel("> System Ready.\n> Neural network initialized.\n> Awaiting command...")
        console.setStyleSheet("background: rgba(0,0,0,0.3); color: #10b981; font-family: 'Consolas'; padding: 15px; border-radius: 8px; font-size: 11px;")
        ol.addWidget(console)
        
        layout.addWidget(ops_card, 2) # Stretch 2 (Wider)
        
        return page

    def _module_activity(self):
        """
        AUDIT LOG (Full Visibility Mode):
        - Top Stats: Total, Critical, Users.
        - Table: 7 Columns with full resize mode.
        """
        page = QWidget(); 
        l = QVBoxLayout(page); 
        l.setContentsMargins(40, 30, 40, 40)
        l.setSpacing(20)
        
        # Header
        h = QHBoxLayout()
        t = QLabel("HISTORIAL DE AUDITORÍA (FORENSE)")
        t.setStyleSheet("font-size: 24px; font-weight: 900; color: white; letter-spacing: 2px;")
        h.addWidget(t); h.addStretch()
        l.addLayout(h)
        
        # --- STATS ROW ---
        stats_row = QHBoxLayout(); stats_row.setSpacing(20)
        
        def mk_stat(title, icon, col):
            c = GlassCard(); c.setFixedHeight(100)
            cl = QHBoxLayout(c); cl.setContentsMargins(25, 15, 25, 15); cl.setSpacing(20)
            
            ic = QLabel(icon); ic.setStyleSheet(f"font-size: 32px; color: {col};")
            cl.addWidget(ic)
            
            vl = QVBoxLayout(); vl.setAlignment(Qt.AlignCenter); vl.setSpacing(5)
            val = QLabel("0"); val.setStyleSheet(f"font-size: 28px; font-weight: 900; color: white;")
            tit = QLabel(title); tit.setStyleSheet("color: #94a3b8; font-weight: 800; font-size: 10px; letter-spacing: 1px;")
            vl.addWidget(val); vl.addWidget(tit)
            cl.addLayout(vl); cl.addStretch()
            return c, val

        c1, self.lbl_log_total = mk_stat("TOTAL REGISTROS", "📜", "#3b82f6")
        c2, self.lbl_log_critical = mk_stat("EVENTOS CRÍTICOS", "🚨", "#ef4444")
        c3, self.lbl_log_users = mk_stat("USUARIOS ÚNICOS", "👥", "#a855f7")
        
        stats_row.addWidget(c1); stats_row.addWidget(c2); stats_row.addWidget(c3)
        l.addLayout(stats_row)
        
        # --- DATA TABLE ---
        t_card = GlassCard(); t_card.setObjectName("glass_card")
        tl = QVBoxLayout(t_card); tl.setContentsMargins(1,1,1,1) # Flush
        
        self.table_audit = QTableWidget(0, 7) # 7 Columns
        self.table_audit.setAlternatingRowColors(True)
        self.table_audit.verticalHeader().setVisible(False)
        self.table_audit.setShowGrid(False)
        
        headers = ["FECHA / HORA", "USUARIO", "ACCIÓN", "SERVICIO / OBJETIVO", "DISPOSITIVO", "DETALLES", "ESTADO"]
        self.table_audit.setHorizontalHeaderLabels(headers)
        
        # Resize Modes for Readability
        hh = self.table_audit.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Interactive) # Allow user resize
        hh.resizeSection(0, 160) # Date
        hh.resizeSection(1, 120) # User
        hh.resizeSection(2, 120) # Action
        hh.resizeSection(3, 150) # Service
        hh.resizeSection(4, 150) # Device
        hh.setSectionResizeMode(5, QHeaderView.Stretch) # Details takes rest
        hh.resizeSection(6, 100) # Status
        
        self.table_audit.setStyleSheet("""
            QTableWidget::item { padding: 8px; font-family: 'Consolas', monospace; font-size: 11px; }
            QHeaderView::section { font-size: 10px; font-weight: 900; color: #cbd5e1; background: #1e293b; padding: 10px; }
        """)

        tl.addWidget(self.table_audit)
        l.addWidget(t_card)
        
        return page

    def _module_admin(self):
        """
        ADMIN PANEL (Command List Style):
        Clean vertical lists of actions for perfect alignment and clarity.
        """
        page = QWidget(); 
        main_layout = QVBoxLayout(page); 
        main_layout.setContentsMargins(50, 40, 50, 50)
        main_layout.setSpacing(30)
        
        # Header
        h = QHBoxLayout()
        t = QLabel("COMANDO CENTRAL (ADMIN)")
        t.setStyleSheet("font-size: 26px; font-weight: 900; color: white; letter-spacing: 2px;")
        h.addWidget(t); h.addStretch()
        main_layout.addLayout(h)
        
        # --- HELPER PARA FILAS DE COMANDO ---
        def add_command_row(layout, icon, title, subtitle, btn_obj, btn_text, color):
            row = QWidget(); 
            rl = QHBoxLayout(row); rl.setContentsMargins(20, 15, 20, 15)
            
            # Icon
            ic = QLabel(icon); ic.setStyleSheet("font-size: 24px;")
            rl.addWidget(ic)
            
            # Textos
            tl = QVBoxLayout(); tl.setSpacing(5)
            l_tit = QLabel(title); l_tit.setStyleSheet(f"color: {color}; font-weight: 800; font-size: 13px; letter-spacing: 0.5px;")
            l_sub = QLabel(subtitle); l_sub.setStyleSheet("color: #64748b; font-size: 11px;")
            tl.addWidget(l_tit); tl.addWidget(l_sub)
            rl.addLayout(tl)
            
            rl.addStretch()
            
            # Button
            btn_obj.setText(f"  {btn_text}  ")
            btn_obj.setCursor(Qt.PointingHandCursor)
            btn_obj.setFixedWidth(180)
            btn_obj.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba{color.replace('rgb', '').replace(')', ', 0.1)')}; 
                    border: 1px solid {color}; 
                    color: {color}; 
                    padding: 10px; 
                    border-radius: 8px; 
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    background-color: {color}; 
                    color: white;
                }}
            """)
            rl.addWidget(btn_obj)
            
            layout.addWidget(row)
            # Separator line
            line = QFrame(); line.setFixedHeight(1); line.setStyleSheet("background: rgba(255,255,255,0.05);")
            layout.addWidget(line)

        # 1. IDENTITY & ACCESS SECTION
        cat_1 = QLabel("GESTIÓN DE IDENTIDAD"); cat_1.setStyleSheet("color: #94a3b8; font-weight: 900; font-size: 10px; letter-spacing: 1px; margin-bottom: 5px;")
        main_layout.addWidget(cat_1)
        
        card_id = GlassCard()
        l_id = QVBoxLayout(card_id); l_id.setContentsMargins(0, 10, 0, 10); l_id.setSpacing(0)
        
        self.btn_manage_users_real = QPushButton()
        add_command_row(l_id, "👥", "USUARIOS DEL SISTEMA", "Crear, editar o desactivar cuentas de acceso.", self.btn_manage_users_real, "GESTIONAR USUARIOS", "#3b82f6")
        
        self.btn_sessions_real = QPushButton()
        add_command_row(l_id, "📡", "RADAR DE SESIONES", "Monitorizar actividad en tiempo real y expulsar intrusos.", self.btn_sessions_real, "VER MONITOR", "#6366f1")
        
        main_layout.addWidget(card_id)
        
        # 2. SECURITY & MAINTENANCE
        cat_2 = QLabel("SEGURIDAD Y MANTENIMIENTO"); cat_2.setStyleSheet("color: #94a3b8; font-weight: 900; font-size: 10px; letter-spacing: 1px; margin-top: 10px; margin-bottom: 5px;")
        main_layout.addWidget(cat_2)
        
        card_sec = GlassCard()
        l_sec = QVBoxLayout(card_sec); l_sec.setContentsMargins(0, 10, 0, 10); l_sec.setSpacing(0)
        
        self.btn_regenerate_2fa = QPushButton()
        add_command_row(l_sec, "🔐", "ROTACIÓN DE LLAVES 2FA", "Regenerar secretos TOTP para todos los usuarios.", self.btn_regenerate_2fa, "ROTAR SECRETOS", "#a855f7")
        
        self.btn_clean_local = QPushButton()
        add_command_row(l_sec, "🧹", "LIMPIEZA DE CACHÉ LOCAL", "Eliminar archivos temporales y optimizar SQLite.", self.btn_clean_local, "LIMPIAR DISCO", "#10b981")
        
        main_layout.addWidget(card_sec)
        
        # 3. DANGER ZONE
        cat_3 = QLabel("ZONA DE RIESGO"); cat_3.setStyleSheet("color: #ef4444; font-weight: 900; font-size: 10px; letter-spacing: 1px; margin-top: 10px; margin-bottom: 5px;")
        main_layout.addWidget(cat_3)
        
        card_danger = GlassCard()
        l_danger = QVBoxLayout(card_danger); l_danger.setContentsMargins(0, 10, 0, 10); l_danger.setSpacing(0)
        
        self.btn_purge = QPushButton()
        add_command_row(l_danger, "☢️", "PURGA TOTAL EN NUBE", "Eliminar irreversiblemente todos los registros remotos.", self.btn_purge, "EJECUTAR PURGA", "#ef4444")
        
        main_layout.addWidget(card_danger)
        
        main_layout.addStretch()
        return page

    def _module_settings(self):
        """
        SETTINGS HUB (Command List Style):
        Clean vertical lists for Preferences, Security, AI, Tools, and Data.
        """
        container = QWidget()
        main_v = QVBoxLayout(container); main_v.setContentsMargins(0,0,0,0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; } QScrollBar:vertical { width: 8px; background: #0F172A; }")
        
        page = QWidget()
        page.setObjectName("settings_page")
        page.setStyleSheet("#settings_page { background-color: #0F172A; }") # Match global background
        l = QVBoxLayout(page)
        l.setContentsMargins(50, 40, 50, 60); l.setSpacing(15)
        
        # Header
        h = QHBoxLayout()
        t = QLabel("CONFIGURACIÓN DEL SISTEMA")
        t.setStyleSheet("font-size: 26px; font-weight: 900; color: white; letter-spacing: 2px;")
        h.addWidget(t); h.addStretch()
        l.addLayout(h)
        l.addSpacing(20)

        # --- HELPER: Settings Row (Icon | Text | Widget) ---
        def add_setting_row(layout, icon, title, subtitle, widget):
            row = QWidget()
            row.setStyleSheet("background-color: rgba(30, 41, 59, 0.3); border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);")
            rl = QHBoxLayout(row); rl.setContentsMargins(20, 15, 20, 15)
            
            ic = QLabel(icon); ic.setStyleSheet("font-size: 24px; color: #94a3b8;")
            rl.addWidget(ic)
            
            tl = QVBoxLayout(); tl.setSpacing(4)
            t_lbl = QLabel(title); t_lbl.setStyleSheet("color: #f8fafc; font-weight: 700; font-size: 13px;")
            s_lbl = QLabel(subtitle); s_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
            tl.addWidget(t_lbl); tl.addWidget(s_lbl)
            rl.addLayout(tl)
            
            rl.addStretch()
            rl.addWidget(widget)
            layout.addWidget(row)

        # --- 1. GLOBAL PREFERENCES ---
        l.addWidget(QLabel("PREFERENCIAS GLOBALES", styleSheet="color: #94a3b8; font-weight: 900; font-size: 10px; letter-spacing: 1px; margin-bottom: 5px;"))
        
        # Language
        self.combo_lang = QComboBox(); self.combo_lang.addItems(["Español (ES)", "English (EN)"])
        self.combo_lang.setFixedWidth(150); self.combo_lang.setStyleSheet("background: #1e293b; color: white; border: 1px solid #334155; padding: 5px;")
        add_setting_row(l, "🌐", "Idioma de Interfaz", "Seleccione su lenguaje preferido.", self.combo_lang)
        
        # Auto-Lock
        self.combo_lock_time = QComboBox(); self.combo_lock_time.addItems(["1 Minuto", "5 Minutos", "10 Minutos", "30 Minutos", "60 Minutos"])
        self.combo_lock_time.setFixedWidth(150); self.combo_lock_time.setStyleSheet("background: #1e293b; color: white; border: 1px solid #334155; padding: 5px;")
        add_setting_row(l, "⏱️", "Bloqueo Automático", "Tiempo de inactividad antes de cerrar sesión.", self.combo_lock_time)

        l.addSpacing(20)

        # --- 2. SECURITY ---
        l.addWidget(QLabel("SEGURIDAD Y CIFRADO", styleSheet="color: #94a3b8; font-weight: 900; font-size: 10px; letter-spacing: 1px; margin-bottom: 5px;"))
        
        # Password Change
        self.btn_change_pwd_real = QPushButton("  CAMBIAR CLAVE  ")
        self.btn_change_pwd_real.setCursor(Qt.PointingHandCursor)
        self.btn_change_pwd_real.setStyleSheet("background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid #3b82f6; font-weight: 700; padding: 8px 16px; border-radius: 6px;")
        add_setting_row(l, "🔑", "Contraseña Maestra", "Actualice su llave principal de cifrado.", self.btn_change_pwd_real)
        
        # Vault Repair
        self.btn_repair_vault_dashboard = QPushButton("  REPARAR INTEGRIDAD  ")
        self.btn_repair_vault_dashboard.setCursor(Qt.PointingHandCursor)
        self.btn_repair_vault_dashboard.setStyleSheet("background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid #f59e0b; font-weight: 700; padding: 8px 16px; border-radius: 6px;")
        add_setting_row(l, "🛠️", "Diagnóstico de Bóveda", "Corregir registros corruptos o huérfanos localmente.", self.btn_repair_vault_dashboard)

        l.addSpacing(20)
        
        # --- 3. AI CONNECTIVITY ---
        l.addWidget(QLabel("INTELIGENCIA ARTIFICIAL", styleSheet="color: #94a3b8; font-weight: 900; font-size: 10px; letter-spacing: 1px; margin-bottom: 5px;"))
        
        # AI Card (Custom for Keys)
        ai_card = QWidget(); ai_card.setStyleSheet("background-color: rgba(30, 41, 59, 0.3); border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);")
        ail = QVBoxLayout(ai_card); ail.setContentsMargins(20, 20, 20, 20); ail.setSpacing(15)
        
        # Provider Row
        pr = QHBoxLayout()
        pr.addWidget(QLabel("🤖", styleSheet="font-size: 24px;"))
        prv_l = QVBoxLayout(); prv_l.setSpacing(4)
        prv_l.addWidget(QLabel("Proveedor de IA", styleSheet="color: #f8fafc; font-weight: 700; font-size: 13px;"))
        prv_l.addWidget(QLabel("Seleccione el motor LLM activo.", styleSheet="color: #64748b; font-size: 11px;"))
        pr.addLayout(prv_l); pr.addStretch()
        self.combo_provider = QComboBox(); self.combo_provider.addItems(["Google Gemini ✨", "OpenAI ChatGPT 🤖", "Anthropic Claude 🛡️"])
        self.combo_provider.setFixedWidth(200); self.combo_provider.setStyleSheet("background: #1e293b; color: white; border: 1px solid #334155; padding: 5px;")
        pr.addWidget(self.combo_provider)
        ail.addLayout(pr)
        
        # Keys Inputs
        keys_grid = QHBoxLayout(); keys_grid.setSpacing(10)
        def mk_key_in(ph): s = QLineEdit(); s.setPlaceholderText(ph); s.setEchoMode(QLineEdit.Password); s.setStyleSheet("background: #0f172a; border: 1px solid #334155; padding: 10px; color: white; border-radius: 6px;"); return s
        self.input_key_gemini = mk_key_in("Gemini API Key")
        self.input_key_chatgpt = mk_key_in("ChatGPT API Key")
        self.input_key_claude = mk_key_in("Claude API Key")
        keys_grid.addWidget(self.input_key_gemini); keys_grid.addWidget(self.input_key_chatgpt); keys_grid.addWidget(self.input_key_claude)
        ail.addLayout(keys_grid)
        
        # Save Button
        self.btn_save_settings = QPushButton("GUARDAR CONFIGURACIÓN Y LLAVES")
        self.btn_save_settings.setCursor(Qt.PointingHandCursor)
        self.btn_save_settings.setStyleSheet("background: #10b981; color: white; font-weight: 900; padding: 12px; border-radius: 8px; border: none;")
        ail.addWidget(self.btn_save_settings)
        
        l.addWidget(ai_card)
        l.addSpacing(20)

        # --- 4. GENERATORS (Simplified) ---
        l.addWidget(QLabel("HERRAMIENTAS", styleSheet="color: #94a3b8; font-weight: 900; font-size: 10px; letter-spacing: 1px; margin-bottom: 5px;"))
        
        # AI Generator Row
        gen_container = QWidget()
        gen_l = QHBoxLayout(gen_container); gen_l.setContentsMargins(0,0,0,0)
        self.input_ai_prompt = QLineEdit(); self.input_ai_prompt.setPlaceholderText("Prompt creativo (ej: nombre de banda de rock)..."); self.input_ai_prompt.setStyleSheet("background: #1e293b; border: 1px solid #334155; padding: 8px; color: white; border-radius: 6px;")
        self.btn_generate_ai = QPushButton(" ✨ GENERAR "); self.btn_generate_ai.setStyleSheet("background: #7c3aed; color: white; font-weight: 700; padding: 8px 16px; border-radius: 6px;")
        gen_l.addWidget(self.input_ai_prompt, 1); gen_l.addWidget(self.btn_generate_ai)
        add_setting_row(l, "🧠", "Generador Contextual (AI)", "Crea contraseñas memorables basadas en frases.", gen_container)

        # Manual Generator (Hidden widgets kept for compatibility)
        self.btn_generate_drawer = QPushButton("ABRIR GENERADOR MANUAL"); self.btn_generate_drawer.setVisible(False)
        self.length_slider = QSlider(Qt.Horizontal); self.length_slider.setVisible(False)
        self.length_label = QLabel(); self.length_label.setVisible(False)
        self.cb_upper = QCheckBox(); self.cb_lower = QCheckBox(); self.cb_digits = QCheckBox(); self.cb_symbols = QCheckBox()
        for c in [self.cb_upper, self.cb_lower, self.cb_digits, self.cb_symbols]: c.setVisible(False)
        # We attach them to page so they are technically 'there'
        hidden_layout = QVBoxLayout(); hidden_layout.addWidget(self.btn_generate_drawer); hidden_layout.addWidget(self.length_slider)
        l.addLayout(hidden_layout)
        
        l.addSpacing(20)

        # Cloud Data (Solo dejamos respaldo nube manual que puede ser útil aquí)
        l.addWidget(QLabel("GESTIÓN DE DATOS (NUBE)", styleSheet="color: #94a3b8; font-weight: 900; font-size: 10px; letter-spacing: 1px; margin-bottom: 5px;"))
        
        cloud_box = QWidget(); cl_l = QHBoxLayout(cloud_box); cl_l.setContentsMargins(0,0,0,0); cl_l.setSpacing(10)
        self.btn_backup = QPushButton("UPLOAD SHAPSHOOT"); self.btn_restore = QPushButton("DOWNLOAD SNAPSHOT")
        for b in [self.btn_backup, self.btn_restore]: b.setCursor(Qt.PointingHandCursor); b.setStyleSheet("background: rgba(6, 182, 212, 0.15); color: #22d3ee; border: 1px solid #06b6d4; font-weight: 700; padding: 8px 16px; border-radius: 6px;")
        cl_l.addWidget(self.btn_backup); cl_l.addWidget(self.btn_restore)
        add_setting_row(l, "☁️", "Snapshot Manual", "Forzar subida/bajada completa.", cloud_box)
        
        # Local Data (Import/Export MOVED TO VAULT)
        # Solo dejamos Backups físicos
        local_box = QWidget(); loc_l = QHBoxLayout(local_box); loc_l.setContentsMargins(0,0,0,0); loc_l.setSpacing(10)
        self.btn_local_backup = QPushButton("BACKUP FS"); self.btn_local_restore = QPushButton("RESTORE FS")
        for b in [self.btn_local_backup, self.btn_local_restore]: 
            b.setCursor(Qt.PointingHandCursor); b.setStyleSheet("background: rgba(148, 163, 184, 0.15); color: #cbd5e1; border: 1px solid #475569; font-weight: 700; padding: 8px 10px; border-radius: 6px; font-size: 10px;")
            loc_l.addWidget(b)
        add_setting_row(l, "📂", "Respaldo Físico (FS)", "Copias de seguridad del archivo .db", local_box)
        
        # Purge
        self.btn_purge_private = QPushButton("  PURGAR DATOS PRIVADOS  ")
        self.btn_purge_private.setCursor(Qt.PointingHandCursor)
        self.btn_purge_private.setStyleSheet("background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid #ef4444; font-weight: 700; padding: 8px 16px; border-radius: 6px;")
        add_setting_row(l, "🔥", "Zona Privada", "Eliminar solo mis registros privados.", self.btn_purge_private)
        
        l.addStretch()
        
        scroll.setWidget(page)
        main_v.addWidget(scroll)
        return container

    def retranslateUi(self): self._load_table()
    def _start_clock(self): self.clock_timer = QTimer(self); self.clock_timer.timeout.connect(self._update_clock); self.clock_timer.start(1000)
    def _update_clock(self): pass
    def _animate_internet(self):
        st = "color: #ef4444;" if not getattr(self, 'internet_online', False) else "color: #10b981;"
        self.status_internet.setText("🌐 OFFLINE" if not getattr(self, 'internet_online', False) else "🌐 ONLINE"); self.status_internet.setStyleSheet(st)
    def _password_strength_icon(self, pwd: str) -> str:
        score = self._score_password(pwd)
        return "🔒" if score >= 70 else "🔓"

    def _score_password(self, pwd: str) -> int:
        if not pwd or pwd == "[⚠️ Error de Llave]": return 0
        s = 0
        if len(pwd) >= 8: s += 20
        if len(pwd) >= 12: s += 20
        if any(c.islower() for c in pwd): s += 20
        if any(c.isupper() for c in pwd): s += 20
        if any(c.isdigit() for c in pwd): s += 10
        if any(c in "!@#$%^&*()-_=+[]{}<>?/|\\;:.,~" for c in pwd): s += 10
        return s
    def _animate_sync(self): pass
    def _animate_supabase(self): pass
