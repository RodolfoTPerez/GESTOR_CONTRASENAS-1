from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QProgressBar, QGridLayout, QScrollArea, QWidget,
    QTextEdit
)
import logging
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QIcon
from src.presentation.widgets.circular_gauge import CircularGauge
from src.presentation.theme_manager import ThemeManager

class AIWorker(QThread):
    finished_signal = pyqtSignal(str)

    def __init__(self, ai_engine, report):
        super().__init__()
        self.ai = ai_engine
        self.report = report
        self.logger = logging.getLogger(__name__)

    def run(self):
        engine_name = getattr(self.ai, 'engine', 'Desconocido')
        try:
            ai_text = self.ai.analyze_vulnerabilities(self.report)
            result = f"🤖 {engine_name.upper()} STRATEGIC ANALYSIS:\n{ai_text}"
        except Exception as e:
            self.logger.error(f"AI Analysis failed for {engine_name}: {e}")
            result = f"⚠️ Error al consultar {engine_name}: {str(e)}"
        self.finished_signal.emit(result)

class HealthDashboardDialog(QDialog):
    def __init__(self, report, guardian_ai, parent=None):
        super().__init__(parent)
        self.report = report
        self.ai = guardian_ai
        self.logger = logging.getLogger(__name__)
        self.setWindowTitle("🛡️ Guardian AI - Security Health Insight")
        self.setMinimumSize(950, 750)
        # [FIX] Rely on the Global Theme State from the Main App
        # Only fallback if absolutely necessary (e.g. standalone launch)
        self.theme = ThemeManager()
        
        # Ensure we use the theme currently active in memory
        if ThemeManager._GLOBAL_THEME:
            self.theme.current_theme = ThemeManager._GLOBAL_THEME
            self.logger.info(f"HealthDashboard using Global Theme: {ThemeManager._GLOBAL_THEME}")

        # [CRITICAL] Enable StyledBackground for QQss to work on QDialog
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        colors = self.theme.get_theme_colors()
        self.setStyleSheet(f"QDialog {{ background-color: {colors['bg']}; }}")
        
        # Load base dialog styles
        base_style = self.theme.load_stylesheet("dialogs")
        if base_style:
            self.setStyleSheet(self.styleSheet() + base_style)
        
        self._setup_ui()
        self.start_ai_analysis()

    def _setup_ui(self):
        colors = self.theme.get_theme_colors()
        
        # Estilos específicos que no están en dialogs.qss o necesitan override
        # [CLEANUP] Estilos específicos (Ya no usamos setProperty, solo stylesheet real)
        # Aplicar el override (truco para no ensuciar el global si hay muchos dialogos)
        # Pero mejor lo inyectamos directo al widget
        self.main_style = f"""
            QFrame#card {{ 
                background-color: {colors['bg_sec']}; 
                border-radius: 18px; 
                border: 1px solid {colors['border']};
            }}
            QFrame#ai_box {{
                background-color: {colors['bg_sec']};
                border: 1px solid {colors['ai']}44;
                border-radius: 18px;
            }}
        """
        # Nota: Mejor inyectamos los estilos extra al final del stylesheet cargado
        self.setStyleSheet(self.theme.load_stylesheet("dialogs") + self.main_style)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)

        # --- TOP SECTION: GAUGE & AI INSIGHTS ---
        top_h_layout = QHBoxLayout()
        top_h_layout.setSpacing(25)

        # Gauge Card
        gauge_card = QFrame()
        gauge_card.setObjectName("card")
        gauge_card.setFixedHeight(220)
        gauge_card.setFixedWidth(300)
        gl = QVBoxLayout(gauge_card)
        gl.setAlignment(Qt.AlignCenter)
        
        score_val = self.report.get("score", 0)
        self.gauge = CircularGauge(self)
        self.gauge.value = score_val
        gl.addWidget(self.gauge)
        
        # Calculate status color based on score (matching CircularGauge logic)
        if score_val < 40:
            status_color = colors["danger"]
        elif score_val < 75:
            status_color = colors["warning"]
        else:
            status_color = colors["success"]
        
        status_lbl = QLabel(self.report.get('status', '---').upper())
        status_lbl.setStyleSheet(f"color: {status_color}; font-weight: 900; font-size: 16px; margin-top: -10px;")
        status_lbl.setAlignment(Qt.AlignCenter)
        gl.addWidget(status_lbl)
        
        top_h_layout.addWidget(gauge_card)

        # AI Insights Card
        ai_card = QFrame()
        ai_card.setObjectName("ai_box")
        ai_card.setFixedHeight(220)
        al = QVBoxLayout(ai_card)
        al.setContentsMargins(20, 20, 20, 20)
        
        ai_lbl = QLabel("🧠 GUARDIAN CISO INSIGHTS (AI)")
        ai_lbl.setStyleSheet(f"color: {colors['ai']}; font-weight: bold; font-size: 11px; letter-spacing: 1px;")
        al.addWidget(ai_lbl)
        
        self.insight_edit = QTextEdit()
        self.insight_edit.setPlainText("⏳ INICIANDO PROTOCOLO DE ENLACE NEURONAL...\n\n> Escaneando vectores de ataque...\n> Analizando entropía de claves...\n> Verificando fugas en Deep Web...\n\n[ESPERANDO RESPUESTA DEL NÚCLEO IA...]")
        self.insight_edit.setReadOnly(True)
        self.insight_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {colors['bg']};
                color: {colors['text']};
                font-family: 'Consolas', monospace;
                font-size: 13px;
                border: 1px solid {colors['border']};
                border-radius: 8px;
                padding: 15px;
            }}
        """)
        al.addWidget(self.insight_edit)
        
        tip_lbl = QLabel("💡 Tip: Usa contraseñas de +16 caracteres con entropía alta.")
        tip_lbl.setObjectName("dialog_subtitle")
        al.addWidget(tip_lbl)
        
        top_h_layout.addWidget(ai_card)
        layout.addLayout(top_h_layout)

        # --- STATS ROW ---
        stats_row = QHBoxLayout()
        stats_row.setSpacing(15)
        
        stats = self.report.get("stats", {})
        u_name = self.report.get("current_user", "USER").upper()
        
        colors = self.theme.get_theme_colors()
        self._add_stat(stats_row, "TOTAL VAULT", stats.get("total", 0), "Registros globales")
        self._add_stat(stats_row, f"MY TOTAL ({u_name})", stats.get("user_total", 0), "Tus registros personales/team")
        self._add_stat(stats_row, "MY VULNERABLE", stats.get("user_weak", 0), "Tus claves débiles", colors["danger"])
        self._add_stat(stats_row, "MY REFUSED", stats.get("user_refused", 0), "Tus errores de llave", colors["danger"])
        
        layout.addLayout(stats_row)

        # --- FINDINGS SECTION ---
        layout.addWidget(QLabel("DETAILED SECURITY FINDINGS"))
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        findings_layout = QVBoxLayout(container)
        findings_layout.setSpacing(12)
        
        findings = self.report.get("findings", [])
        if not findings:
            empty = QLabel("✨ System Clean: No major security threats detected.")
            empty.setStyleSheet(f"color: {colors['success']}; font-weight: bold; font-size: 15px; padding: 40px;")
            empty.setAlignment(Qt.AlignCenter)
            findings_layout.addWidget(empty)
        else:
            for find in findings:
                f_card = QFrame()
                colors = self.theme.get_theme_colors()
                border_color = colors['danger'] if find['type']=='danger' else colors['warning'] if find['type']=='warning' else colors['primary']
                f_card.setStyleSheet(f"""
                    background-color: {colors['bg_sec']}; border-radius: 12px; 
                    border: 1px solid {colors['border']}; border-left: 5px solid {border_color};
                """)
                fl = QVBoxLayout(f_card)
                fl.setContentsMargins(15, 12, 15, 12)
                
                title_h = QHBoxLayout()
                icon = "🚨" if find['type']=='danger' else "⚠️" if find['type']=='warning' else "ℹ️"
                t = QLabel(f"{icon} {find['title']}")
                t.setObjectName("dialog_title")
                t.setStyleSheet("font-size: 14px;")
                title_h.addWidget(t)
                title_h.addStretch()
                fl.addLayout(title_h)
                
                d = QLabel(find["desc"])
                d.setObjectName("dialog_subtitle")
                d.setWordWrap(True)
                fl.addWidget(d)
                
                findings_layout.addWidget(f_card)
        
        findings_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

        # --- FOOTER ---
        footer = QHBoxLayout()
        footer.addStretch()
        close_btn = QPushButton("ACKNOWLEDGMENT & CLOSE")
        close_btn.setFixedWidth(250)
        close_btn.setObjectName("btn_primary")
        close_btn.clicked.connect(self.accept)
        footer.addWidget(close_btn)
        layout.addLayout(footer)

    def _add_stat(self, layout, label, value, desc, color=None):
        card = QFrame()
        card.setObjectName("card")
        l = QVBoxLayout(card)
        l.setContentsMargins(20, 20, 20, 20)
        
        # Obtener colores del tema actual
        colors = self.theme.get_theme_colors()
        # [FIX] Por defecto usar color de texto blanco para los números (Look Profesional)
        # Solo usar color si es semántico (Danger/Success)
        final_color = color if color else colors['text']

        lbl_up = QLabel(label)
        lbl_up.setObjectName("stat_label")
        
        lbl_val = QLabel(str(value))
        lbl_val.setObjectName("stat_val")
        lbl_val.setStyleSheet(f"color: {final_color};")
        
        lbl_desc = QLabel(desc)
        lbl_desc.setStyleSheet(f"color: {colors['text_dim']}; font-size: 11px;")
        
        l.addWidget(lbl_up)
        l.addWidget(lbl_val)
        l.addWidget(lbl_desc)
        layout.addWidget(card)

    def start_ai_analysis(self):
        self.worker = AIWorker(self.ai, self.report)
        self.worker.finished_signal.connect(self.update_ai_insight)
        self.worker.start()

    def update_ai_insight(self, text):
        self.insight_edit.setPlainText(text)
