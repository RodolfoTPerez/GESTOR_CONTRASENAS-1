from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QLinearGradient, QFont, QBrush, QPen
from src.presentation.theme_manager import ThemeManager

class PulseBar(QWidget):
    """A single tactical pulse bar with neon gradient and value-based coloring."""
    def __init__(self, label, parent=None):
        super().__init__(parent)
        self.label_text = label
        self.value = 50 # 0 to 100
        self.setFixedHeight(30)
        self.theme = ThemeManager()
        
    def setValue(self, val):
        self.value = max(0, min(100, val))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        colors = self.theme.get_theme_colors()
        
        # [SENIOR FIX] respect global opacity
        dimmer = getattr(self.theme, '_GLOBAL_OPACITY', 1.0)
        
        # 1. Label
        label_color = QColor(colors["text_dim"])
        is_ghost = self.property("ghost") == "true"
        if is_ghost: 
            label_color.setAlpha(int(178 * dimmer)) # 70% HUD Header
        else:
            label_color.setAlpha(int(255 * dimmer))
        
        painter.setPen(label_color)
        
        # [ATOMIC REFACTOR] Use Centralized Font
        # Old: font = QFont("Segoe UI", 9)
        font = self.theme.get_font("label")
        painter.setFont(font)
        
        # Vertical centering adjustment based on font stats could be added here
        painter.drawText(0, 19, self.label_text) # Adjusted Y slightly for new font alignment
        
        # 2. Bar Background (Theme Aware)
        bar_x = 90
        bar_w = self.width() - bar_x - 10
        bar_h = 6
        bar_y = 12
        
        painter.setPen(Qt.NoPen)
        # Use border color with alpha for track background
        bg_col = QColor(colors["border"])
        bg_col.setAlpha(int(40 * dimmer))
        painter.setBrush(QBrush(bg_col))
        painter.drawRoundedRect(bar_x, bar_y, bar_w, bar_h, 5, 5)
        
        # 3. Bar Fill (Gradient)
        fill_w = int(bar_w * (self.value / 100.0))
        if fill_w > 0:
            # Color logic using Theme Variables
            if self.value > 80:
                c1 = colors["success"]
                c2 = colors["success"] 
            elif self.value > 40:
                c1 = colors["primary"]
                c2 = colors["info"]
            else:
                c1 = colors["danger"]
                c2 = colors["danger"]
                
            c1_q, c2_q = QColor(c1), QColor(c2)
            c2_q = c2_q.lighter(110)
 
            if is_ghost: 
                # Fills use GLASSY alpha
                is_urgent = (c1_q.red() > 200) # Check urgency based on the first color
                alpha = int(0.40 * 255 * dimmer) if is_urgent else int(0.20 * 255 * dimmer) 
                c1_q.setAlpha(alpha)
                c2_q.setAlpha(alpha)
            else:
                # Normal mode also needs dimmer!
                c1_q.setAlpha(int(255 * dimmer))
                c2_q.setAlpha(int(255 * dimmer))
 
            gradient = QLinearGradient(bar_x, 0, bar_x + fill_w, 0)
            gradient.setColorAt(0, c1_q)
            gradient.setColorAt(1, c2_q)
            
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(bar_x, bar_y, fill_w, bar_h, 5, 5)
            
            # 4. Neon Glow (Inner) - Border (80% for Ghost)
            pen_color = QColor(c2) # Use the second color for the border
            if is_ghost:
                pen_color.setAlpha(int(204 * dimmer)) 
            else:
                pen_color.setAlpha(int(255 * dimmer)) # Solid for non-ghost mode
            
            painter.setPen(QPen(pen_color, 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(bar_x, bar_y, fill_w, bar_h, 5, 5)

class TacticalPulseBars(QFrame):
    """
    Group of Tactical Pulse Bars.
    Drop-in replacement for the Radar Chart data structure.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tactical_pulse_container")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(10)
        
        self.labels = ["STRENGTH", "AUTH", "SYNC", "HEALTH", "ROTATION"]
        self.bars = {}
        
        for lbl in self.labels:
            bar = PulseBar(lbl)
            self.bars[lbl] = bar
            self.layout.addWidget(bar)
            
    def setValues(self, values: list):
        """Expects 5 float/int values [0-100] mapping to labels order."""
        if len(values) >= 5:
            for i in range(5):
                lbl = self.labels[i]
                self.bars[lbl].setValue(values[i])
