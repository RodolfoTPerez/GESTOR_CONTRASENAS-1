from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt, pyqtProperty

class TacticalMetricUnit(QWidget):
    def __init__(self, title, show_bar=True, parent=None):
        super().__init__(parent)
        self.show_bar = show_bar
        self.setFixedHeight(44) # Optimized for high-density cards
        l = QVBoxLayout(self); l.setContentsMargins(0, 0, 0, 0); l.setSpacing(6)
        
        info = QHBoxLayout(); info.setSpacing(10); info.setContentsMargins(0, 0, 0, 0)
        self.lbl_title = QLabel(title.upper()); self.lbl_title.setObjectName("tactical_metric_title")
        self.lbl_value = QLabel("--"); self.lbl_value.setObjectName("tactical_metric_label")
        
        info.addWidget(self.lbl_title); info.addStretch(); info.addWidget(self.lbl_value)
        l.addLayout(info)
        
        self.bar_container = QFrame()
        self.bar_container.setObjectName("tactical_bar_container")
        self.bar_container.setFixedHeight(8) 
        self.bar_layout = QHBoxLayout(self.bar_container); self.bar_layout.setContentsMargins(0,0,0,0); self.bar_layout.setSpacing(0)
        self.bar_fill = QFrame()
        self.bar_fill.setObjectName("tactical_bar_fill")
        self.bar_fill.setFixedHeight(8)
        self.bar_spacer = QWidget()
        self.bar_layout.addWidget(self.bar_fill, 0)
        self.bar_layout.addWidget(self.bar_spacer, 100)
        l.addWidget(self.bar_container)
        
        if not self.show_bar:
            self.bar_container.hide()
            self.bar_fill.hide()

    def set_title(self, title):
        """Updates the metric title dynamically for i18n support."""
        if hasattr(self, 'lbl_title'):
            self.lbl_title.setText(title.upper())

    def set_value(self, text, percent=None, color_name=None):
        """
        Updates the metric value and visual state.
        color_name: 'success', 'warning', 'danger', 'info'
        """
        self.lbl_value.setText(text)
        if color_name:
            self.lbl_value.setProperty("status", color_name)
            self.bar_fill.setProperty("status", color_name)
            self.lbl_value.style().unpolish(self.lbl_value)
            self.lbl_value.style().polish(self.lbl_value)
            self.bar_fill.style().unpolish(self.bar_fill)
            self.bar_fill.style().polish(self.bar_fill)
        
        if self.show_bar and percent is not None:
            p = max(2, min(100, int(percent)))
            self.bar_layout.setStretch(0, p)
            self.bar_layout.setStretch(1, 100 - p)

    # [ATOMIC] Opacity Property for Global Dimmer cascading
    def get_opacity(self):
        return self._opacity

    def set_opacity(self, opacity):
        self._opacity = opacity
        # Propagate to children if needed, though QSS usually handles color alpha
        pass

    _opacity = 1.0
    opacity = pyqtProperty(float, get_opacity, set_opacity)
