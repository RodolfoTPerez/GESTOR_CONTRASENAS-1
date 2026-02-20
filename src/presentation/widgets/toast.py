from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGraphicsOpacityEffect, QFrame, QApplication
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QSize
from PyQt5.QtGui import QColor, QFont
from src.presentation.theme_manager import ThemeManager

class ToastNotification(QWidget):
    """
    Notificación flotante moderna (Toast) con estilo Cyber-Ops.
    """
    def __init__(self, parent=None, title="", message="", icon="ℹ️", accent_color="#06b6d4", duration=3000):
        super().__init__(parent)
        self.theme = ThemeManager()
        
        # Banderas para que sea un overlay sin marco y siempre visible
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint | Qt.SubWindow | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.accent_color = accent_color
        self.duration_ms = duration
        
        # Tamaño flexible para soportar reportes largos
        self.setMinimumWidth(400)
        self.setMaximumWidth(450)
        
        # Estilo base del widget usando Tokens
        self.setStyleSheet(self.theme.apply_tokens(f"""
            QWidget {{
                background: transparent;
            }}
            QFrame#card {{
                background-color: @bg_dashboard_card;
                border: 1px solid @border;
                border-left: 4px solid {self.accent_color};
                border-radius: @border-radius-main;
            }}
            QLabel {{
                color: @text;
                background: transparent;
                border: none;
            }}
        """))
        
        # Layout Principal
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Tarjeta contenedora
        self.card = QFrame()
        self.card.setObjectName("card")
        
        # Sombra
        # (Nota: Las sombras complejas en Qt a veces causan lag, usamos borde sutil en su lugar)
        
        self.card_layout = QHBoxLayout(self.card)
        self.card_layout.setContentsMargins(15, 10, 15, 10)
        self.card_layout.setSpacing(15)
        
        # Icono (Emoji o Texto)
        self.icon_lbl = QLabel(icon)
        font_icon = QFont()
        font_icon.setPixelSize(24)
        self.icon_lbl.setFont(font_icon)
        self.card_layout.addWidget(self.icon_lbl)
        
        # Textos
        self.text_layout = QVBoxLayout()
        self.text_layout.setSpacing(2)
        
        self.title_lbl = QLabel(title.upper())
        font_title = QFont()
        font_title.setPixelSize(11)
        font_title.setBold(True)
        font_title.setLetterSpacing(QFont.AbsoluteSpacing, 1.0)
        self.title_lbl.setFont(font_title)
        self.title_lbl.setStyleSheet(f"color: {accent_color}; opacity: 0.9;")
        
        self.msg_lbl = QLabel(message)
        font_msg = QFont()
        font_msg.setPixelSize(13)
        self.msg_lbl.setFont(font_msg)
        self.msg_lbl.setWordWrap(True)
        
        self.text_layout.addWidget(self.title_lbl)
        self.text_layout.addWidget(self.msg_lbl)
        
        self.card_layout.addLayout(self.text_layout)
        self.main_layout.addWidget(self.card)
        
        # Animación de Opacidad (Fade In/Out)
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0) # Iniciar invisible
        
        self.anim_op = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim_op.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Animación de Posición (Slide Up)
        self.anim_pos = QPropertyAnimation(self, b"pos")
        self.anim_pos.setEasingCurve(QEasingCurve.OutBack)
        
        # Timer de auto-cierre
        self.timer_close = QTimer(self)
        self.timer_close.setSingleShot(True)
        self.timer_close.timeout.connect(self.start_close)

    def show_animated(self):
        self.show()
        
        # Fade In
        self.anim_op.setDuration(300)
        self.anim_op.setStartValue(0)
        self.anim_op.setEndValue(1)
        self.anim_op.start()
        
        # Iniciar timer
        self.timer_close.start(self.duration_ms)
        
    def start_close(self):
        # Fade Out
        self.anim_op.setDuration(400)
        self.anim_op.setStartValue(1)
        self.anim_op.setEndValue(0)
        self.anim_op.finished.connect(self.close)
        self.anim_op.start()
