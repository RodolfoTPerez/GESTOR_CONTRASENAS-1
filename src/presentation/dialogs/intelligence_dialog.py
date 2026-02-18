import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QFrame, QApplication, QShortcut
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from src.domain.messages import MESSAGES
from src.presentation.theme_manager import ThemeManager

logger = logging.getLogger(__name__)

class IntelligenceDialog(QDialog):
    def __init__(self, report, ai_engine, parent=None):
        super().__init__(parent)
        self.report = report
        self.ai_engine = ai_engine
        self.setWindowTitle("Guardian AI Assistant 🧠")
        self.setFixedSize(550, 700)
        from PyQt5.QtCore import QSettings
        self.settings = QSettings(ThemeManager.APP_ID, "VultraxCore_Global")
        self.theme = ThemeManager()
        active_theme = self.settings.value("theme_active", "tactical_dark")
        self.theme.set_theme(active_theme)
        
        # Fondo base instantáneo para evitar flasheo blanco
        colors = self.theme.get_theme_colors()
        self.setStyleSheet(f"QDialog {{ background-color: {colors['bg']}; }}")
        self.setStyleSheet(self.theme.load_stylesheet("dialogs"))

        self._init_ui()
        self._show_findings()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header Score
        score_frame = QFrame()
        score_frame.setObjectName("card")
        score_layout = QVBoxLayout(score_frame)
        
        score_val = self.report.get("score")
        status = self.report.get("status", "Desconocido")

        if isinstance(score_val, (int, float)):
            display_score = f"{int(score_val)}%"
            numeric_score = score_val
        else:
            display_score = "N/A"
            numeric_score = None

        lbl_score = QLabel(display_score)
        colors = self.theme.get_theme_colors()
        color = colors["success"] if (numeric_score is not None and numeric_score > 80) else colors["warning"] if (numeric_score is not None and numeric_score > 50) else colors["danger"]
        if numeric_score is None: color = colors["text_dim"]
        lbl_score.setStyleSheet(f"font-size: 48px; font-weight: bold; color: {color};")
        lbl_score.setAlignment(Qt.AlignCenter)
        
        lbl_title = QLabel(f"Salud de la Bóveda: {status}")
        lbl_title.setObjectName("main_title")
        lbl_title.setStyleSheet("font-size: 16px;")
        lbl_title.setAlignment(Qt.AlignCenter)
        
        score_layout.addWidget(lbl_score)
        score_layout.addWidget(lbl_title)
        layout.addWidget(score_frame)

        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        layout.addWidget(self.content_text)

        # Nav layout
        nav_layout = QHBoxLayout()
        for text, slot in [("↑ Subir", self._scroll_up), ("↓ Bajar", self._scroll_down), ("⤒ Top", self._scroll_top), ("⤓ Bottom", self._scroll_bottom)]:
            btn = QPushButton(text)
            btn.setObjectName("btn_secondary")
            btn.clicked.connect(slot)
            nav_layout.addWidget(btn)
        layout.addLayout(nav_layout)

        # Shortcuts
        QShortcut(QKeySequence("PgUp"), self, activated=self._scroll_up)
        QShortcut(QKeySequence("PgDown"), self, activated=self._scroll_down)
        QShortcut(QKeySequence("Home"), self, activated=self._scroll_top)
        QShortcut(QKeySequence("End"), self, activated=self._scroll_bottom)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        self.btn_findings = QPushButton("Hallazgos Locales")
        self.btn_findings.setObjectName("btn_secondary")
        self.btn_findings.clicked.connect(self._show_findings)
        btn_layout.addWidget(self.btn_findings)
 
        self.btn_geminis = QPushButton("Análisis Profundo Gemini")
        self.btn_geminis.setObjectName("btn_primary") # Reutilizar btn_primary para el gradiente (se puede personalizar en QSS)
        self.btn_geminis.clicked.connect(self._on_geminis_click)
        btn_layout.addWidget(self.btn_geminis)
        layout.addLayout(btn_layout)

        self.lbl_ai_engine = QLabel(f"Motor IA: {self.ai_engine.engine}")
        # [FIX] Use theme primary color
        self.lbl_ai_engine.setStyleSheet(f"color: {colors['primary']}; font-size: 12px; font-weight: bold;")
        layout.addWidget(self.lbl_ai_engine)

        btn_close = QPushButton("Cerrar")
        btn_close.setObjectName("btn_secondary")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def _show_findings(self):
        html = f"<h3>{MESSAGES.AI.TITLE_HEAD}</h3>"
        if not self.report["findings"]:
            html += f"<p style='color: {colors['success']};'>{MESSAGES.AI.TEXT_NO_VULNS}</p>"
        else:
            for f in self.report["findings"]:
                f_color = colors["danger"] if f["type"] == "danger" else colors["warning"] if f["type"] == "warning" else colors["primary"]
                icon = "🚨" if f["type"] == "danger" else "⚠️" if f["type"] == "warning" else "ℹ️"
                html += f"<div style='margin-bottom: 12px; margin-top: 10px;'>" \
                        f"<b style='color: {f_color};'>{icon} {f['title']}</b><br/>" \
                        f"<span style='color: {colors['text_dim']};'>{f['desc']}</span>" \
                        f"</div>"
        self.content_text.setHtml(html)
        self.content_text.setFocus()
        try:
            sb = self.content_text.verticalScrollBar()
            sb.setValue(sb.minimum())
        except Exception as e:
            logger.debug(f"Scrollbar reset failed: {e}")

    def _scroll_up(self):
        try:
            sb = self.content_text.verticalScrollBar()
            sb.setValue(max(sb.value() - sb.pageStep(), sb.minimum()))
        except Exception as e:
            logger.debug(f"Scroll up failed: {e}")

    def _scroll_down(self):
        try:
            sb = self.content_text.verticalScrollBar()
            sb.setValue(min(sb.value() + sb.pageStep(), sb.maximum()))
        except Exception as e:
            logger.debug(f"Scroll down failed: {e}")

    def _scroll_top(self):
        try:
            sb = self.content_text.verticalScrollBar()
            sb.setValue(sb.minimum())
        except Exception as e:
            logger.debug(f"Scroll top failed: {e}")

    def _scroll_bottom(self):
        try:
            sb = self.content_text.verticalScrollBar()
            sb.setValue(sb.maximum())
        except Exception as e:
            logger.debug(f"Scroll bottom failed: {e}")

    def _on_geminis_click(self):
        ai = self.ai_engine
        engine = ai.engine
        if self.ai_engine.engine == "Gemini" and not self.api_key:
            PremiumMessage.information(self, MESSAGES.AI.TITLE_SETUP_REQ, MESSAGES.AI.TEXT_GEMINI_SETUP)
            return
        elif self.ai_engine.engine == "ChatGPT" and not self.api_key:
            PremiumMessage.information(self, MESSAGES.AI.TITLE_SETUP_REQ, MESSAGES.AI.TEXT_CHATGPT_SETUP)
            return

        if not PremiumMessage.question(self, MESSAGES.AI.TITLE_CONFIRM, MESSAGES.AI.TEXT_CONFIRM):
             return

        # [FIX] Use theme primary color for title and text for body
        colors = self.theme.get_theme_colors()
        self.content_text.setHtml(f"<h3 style='color: {colors['primary']};'>{MESSAGES.AI.TEXT_CONSULTING.format(engine=engine)}</h3><p style='color: {colors['text']};'>{MESSAGES.AI.TEXT_THINKING}</p>")
        QApplication.processEvents()

        try:
            safe_report = ai.sanitize_report_for_ai(self.report)
        except Exception as e:
            logger.debug(f"AI report sanitization failed: {e}")
            safe_report = self.report

        if engine == "Gemini":
            summary = ai.gemini.analyze_vulnerabilities(safe_report)
        else:
            summary = ai.chatgpt.ask(str(safe_report))
        
        summary_html = summary.replace('\n', '<br>')
        # [FIX] Use theme text color for AI response (avoids invisible text on white bg)
        colors = self.theme.get_theme_colors()
        html = f"<h3>{MESSAGES.AI.TITLE_EXPERT.format(engine=engine)}</h3><p style='color: {colors['text']}; line-height: 1.5;'>{summary_html}</p>"
        self.content_text.setHtml(html)
