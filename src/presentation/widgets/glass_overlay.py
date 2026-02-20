from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QGraphicsOpacityEffect, QGraphicsBlurEffect
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QSize
from PyQt5.QtGui import QColor, QPainter, QBrush, QPen
from src.presentation.theme_manager import ThemeManager

class GlassOverlay(QWidget):
    """
    Overlay de cristal para confirmaciones modales "In-Place".
    Bloquea la interfaz subyacente con un efecto de desenfoque y oscurecimiento.
    """
    answer_selected = pyqtSignal(bool) # True=Yes, False=No

    def __init__(self, parent_widget, title, message, icon="❓"):
        super().__init__(parent_widget)
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        self.theme = ThemeManager()
        
        # Cubrir todo el padre
        self.resize(parent_widget.size())
        
        # Color de fondo dinamico
        colors = self.theme.get_theme_colors()
        bg_rgb = colors.get('bg', '#0a0f1d')
        # Convert hex to QColor to get loose RGB
        c = QColor(bg_rgb)
        self.bg_color_base = QColor(c.red(), c.green(), c.blue(), 200) # Base para paintEvent
        
        # Layout principal centrado
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)
        
        # [SENIOR FIX] Restore Glass Transparency
        # The theme returns solid hex for tactical (#0f172a), but we need RGBA for glass effect.
        # We parse the theme color and apply alpha programmatically.
        card_bg_hex = colors.get("bg_dashboard_card", "#0f172a")
        if card_bg_hex.startswith("#"):
            c_bg = QColor(card_bg_hex)
            # 242 = 0.95 alpha approx (Visible but slightly transparent)
            bg_style = f"rgba({c_bg.red()}, {c_bg.green()}, {c_bg.blue()}, 0.95)"
        else:
            bg_style = card_bg_hex # Already RGBA or named
            
        # Border also needs transparency if not provided
        border_val = colors.get("border", "rgba(255, 255, 255, 0.1)")
        
        # Tarjeta de Diálogo
        self.card = QFrame()
        self.card.setObjectName("glass_card")
        self.card.setFixedSize(400, 220)
        self.card.setStyleSheet(self.theme.apply_tokens(f"""
            QFrame#glass_card {{
                background-color: {bg_style};
                border: 1px solid {border_val};
                border-radius: @border-radius-main;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """))
        
        # Contenido de la tarjeta
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(30, 30, 30, 30)
        self.card_layout.setSpacing(15)
        
        # Icono y Título
        self.h_header = QHBoxLayout()
        self.icon_lbl = QLabel(icon)
        self.icon_lbl.setStyleSheet("font-size: 32px;")
        
        self.title_lbl = QLabel(title.upper())
        self.title_lbl.setStyleSheet(self.theme.apply_tokens("color: @text; font-weight: 900; font-size: 14px; letter-spacing: 1px;"))
        
        self.h_header.addWidget(self.icon_lbl)
        self.h_header.addWidget(self.title_lbl)
        self.h_header.addStretch()
        
        # Mensaje
        self.msg_lbl = QLabel(message)
        self.msg_lbl.setWordWrap(True)
        self.msg_lbl.setStyleSheet(self.theme.apply_tokens("color: @text_dim; font-size: 13px; font-weight: 500; line-height: 1.4;"))
        
        # Botones
        self.h_btns = QHBoxLayout()
        self.h_btns.setSpacing(15)
        
        self.btn_yes = QPushButton("CONFIRMAR")
        self.btn_no = QPushButton("CANCELAR")
        
        for btn in [self.btn_yes, self.btn_no]:
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(40)
            
        self.btn_yes.setStyleSheet(self.theme.apply_tokens("""
            QPushButton {
                background-color: @primary;
                color: @text_on_primary;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
                letter-spacing: 0.5px;
            }
            QPushButton:hover { background-color: @accent; }
        """))
        
        self.btn_no.setStyleSheet(self.theme.apply_tokens("""
            QPushButton {
                background-color: transparent;
                color: @text_dim;
                border: 1px solid @border;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background-color: @border; color: @text; }
        """))
        
        self.btn_yes.clicked.connect(lambda: self.on_answer(True))
        self.btn_no.clicked.connect(lambda: self.on_answer(False))
        
        self.h_btns.addWidget(self.btn_no)
        self.h_btns.addWidget(self.btn_yes)
        
        self.card_layout.addLayout(self.h_header)
        self.card_layout.addWidget(self.msg_lbl)
        self.card_layout.addStretch()
        self.card_layout.addLayout(self.h_btns)
        
        self.layout.addWidget(self.card)
        
        # Efectos visuales
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
        
        # Animaciones
        self.anim_fade = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim_fade.setDuration(250)
        self.anim_fade.setEasingCurve(QEasingCurve.OutQuad)
        
        # Animación de escala (Pop-in)
        # Nota: QPropertyAnimation no anima scale directamente en QWidget sin transformaciones complejas, 
        # así que usaremos geometría o simplemente fade por simplicidad y rendimiento.
        
    def show_modal(self):
        self.show()
        self.anim_fade.setStartValue(0)
        self.anim_fade.setEndValue(1)
        self.anim_fade.start()
        
    def on_answer(self, result):
        self.anim_fade.setStartValue(1)
        self.anim_fade.setEndValue(0)
        self.anim_fade.finished.connect(lambda: self.finalize(result))
        self.anim_fade.start()
        
    def finalize(self, result):
        self.answer_selected.emit(result)
        self.close()

    def paintEvent(self, event):
        # Dibujar el fondo semitransparente manualmente
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), self.bg_color_base)
