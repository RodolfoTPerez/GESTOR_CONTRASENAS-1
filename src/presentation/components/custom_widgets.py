from PyQt5.QtWidgets import QPushButton, QWidget
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QRectF
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QLinearGradient

class TableEyeButton(QPushButton):
    def __init__(self, row, callback_show, callback_hide, parent=None):
        super().__init__("👁️", parent)
        self.row_index = row # Usamos row_index para evitar colisión con propiedades de Qt
        self.callback_show = callback_show
        self.callback_hide = callback_hide
        self.setFlat(True)
        self.setObjectName("table_eye_btn")
        self.setFixedSize(30, 30) 
        self.setCursor(Qt.PointingHandCursor)
        self.setFlat(True)

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._auto_hide)
        self.clicked.connect(self._toggle)

    def _toggle(self):
        if self.text() == "👁️":
            self.setText("🙈")
            # SENIOR: Pasamos el objeto botón directamente para que el receptor 
            # determine la fila actual mediante coordenadas (resistente a ordenamiento)
            self.callback_show(self) 
            self.timer.start(2500)
        else:
            self._auto_hide()

    def _auto_hide(self):
        self.setText("👁️")
        self.callback_hide(self)

class ThemeSelectorSwitch(QPushButton):
    themeChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 28)
        self.setCursor(Qt.PointingHandCursor)
        from src.presentation.theme_manager import ThemeManager
        self.tm = ThemeManager()
        self.themes = ["tactical_dark", "saas_commercial", "obsidian_flow", "bunker_ops"]
        self.current_index = 0
        
    def next_theme(self):
        self.current_index = (self.current_index + 1) % len(self.themes)
        theme_id = self.themes[self.current_index]
        self.themeChanged.emit(theme_id)
        self.update()

    def refresh_theme(self):
        self.update()

    def mousePressEvent(self, event):
        self.next_theme()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        colors = self.tm.get_theme_colors()
        bg_color = QColor(colors.get("primary", "#3b82f6"))
        
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 14, 14)
        
        margin = 3
        radius = self.height() - (margin * 2)
        available_width = self.width() - radius - (margin * 2)
        step = available_width / (len(self.themes) - 1)
        x_pos = margin + (self.current_index * step)
        
        painter.setBrush(QColor(colors.get("text_on_primary", "#ffffff")))
        painter.drawEllipse(int(x_pos), margin, radius, radius)

class ToggleSwitch(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setMinimumWidth(50)
        self.setMaximumWidth(50)
        self.setMinimumHeight(24)
        self.setCursor(Qt.PointingHandCursor)
        from src.presentation.theme_manager import ThemeManager
        self.tm = ThemeManager()
        self.refresh_theme()
        self.toggled.connect(self.refresh_theme)

    def refresh_theme(self):
        colors = self.tm.get_theme_colors()
        primary = colors.get("primary", "#3b82f6")
        bg_sec = colors.get("bg_sec", "#161d31")
        border_radius = colors.get("border-radius-main", "12px")
        
        bg_color = primary if self.isChecked() else bg_sec
        border = f"1px solid {colors.get('border', 'rgba(255,255,255,0.1)')}" if not self.isChecked() else "none"
        
        style = f"""
            QPushButton {{
                background-color: {bg_color};
                border-radius: {border_radius};
                border: {border};
            }}
        """
        self.setStyleSheet(style)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        colors = self.tm.get_theme_colors()
        radius = self.height() - 4
        margin = 2
        
        if self.isChecked():
            x = self.width() - radius - margin
            color = QColor(colors.get("text_on_primary", "#ffffff"))
        else:
            x = margin
            color = QColor(colors.get("text_dim", "#94a3b8"))
            
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(x), margin, radius, radius)


# NOTE: CircularGauge and HealthReactorWidget moved to src/presentation/widgets/

