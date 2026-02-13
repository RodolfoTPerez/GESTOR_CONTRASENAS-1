from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygonF
from src.presentation.theme_manager import ThemeManager

class EncryptionStatusWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setFixedWidth(195)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._status = "SECURE"
        self._text = "AES-256 ENCRYPTED"
        self.theme = ThemeManager()
        
    def setStatus(self, status: str, text: str = None):
        self._status = status
        if text: self._text = text
        self.update()
        
    def refresh_theme(self):
        self.theme = ThemeManager()
        self.update()

    def paintEvent(self, event):
        colors = self.theme.get_theme_colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self._status == "SECURE":
            c = QColor(colors["success"])
        elif self._status == "WARNING":
            c = QColor(colors["warning"])
        else:
            c = QColor(colors["danger"])

        is_ghost = self.property("ghost") == "true"
        if is_ghost:
            painter.setPen(QPen(QColor(c.red(), c.green(), c.blue(), 76), 1)) # 30% for Ghost (Senior: Increased from 10%)
            painter.setBrush(QColor(c.red(), c.green(), c.blue(), 38)) # 15% for Ghost (Senior: Increased from 5%)
        else:
            painter.setPen(QPen(QColor(c.red(), c.green(), c.blue(), 60), 1))
            painter.setBrush(QColor(c.red(), c.green(), c.blue(), 20))
        painter.drawRoundedRect(QRectF(2, 6, self.width()-4, self.height()-12), 8, 8)
        
        # Shield (Icon)
        ix, iy = 15, self.height() / 2
        shield_color = QColor(c)
        if is_ghost: shield_color.setAlpha(178) # 70% HUD Icon (Senior: Increased from 40%)
        painter.setPen(QPen(shield_color, 1.5)); painter.setBrush(Qt.NoBrush)
        shield = QPolygonF([QPointF(ix, iy-7), QPointF(ix+6, iy-5), QPointF(ix+6, iy+2), QPointF(ix, iy+8), QPointF(ix-6, iy+2), QPointF(ix-6, iy-5)])
        painter.drawPolygon(shield)
        
        # Text (HUD Label)
        text_color = QColor(c)
        if is_ghost: text_color.setAlpha(204) # 80% Legend (Senior: Increased from 40%)
        painter.setPen(text_color)
        font = QFont("Inter", 8, QFont.Bold); font.setLetterSpacing(QFont.AbsoluteSpacing, 1.2)
        painter.setFont(font)
        painter.drawText(QRectF(25, 0, self.width()-30, self.height()), Qt.AlignCenter, self._text)
