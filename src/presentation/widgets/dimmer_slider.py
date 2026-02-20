from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QApplication
from PyQt5.QtCore import Qt, pyqtSignal
from src.presentation.theme_manager import ThemeManager


class DimmerSlider(QWidget):
    """
    Tactical Dimmer Slider for granular opacity control.
    
    CORRECT FLOW:
    1. User moves slider
    2. _on_value_changed() calls ThemeManager.set_global_opacity()
       -> This clears ThemeManager cache automatically
    3. Emits opacity_changed(float) so Dashboard can
       call set_dimmer_opacity() on ALL cards
    4. Each card calls refresh_styles() -> re-reads QSS with new opacity
    """

    opacity_changed = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme = ThemeManager()
        self._setup_ui()
        self.refresh_styles()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)

        self.label = QLabel("🔆 OPACITY DIMMER")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(20)
        self.slider.setMaximum(100)
        # Initialize from current global state to ensure sync
        self.slider.setValue(int(ThemeManager._GLOBAL_OPACITY * 100))
        self.slider.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.slider)

        self.value_label = QLabel(f"{int(ThemeManager._GLOBAL_OPACITY * 100)}%")
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)

    def _on_value_changed(self, value: int):
        """
        Step 1: Update global state FIRST.
        Step 2: Provide visual feedback.
        Step 3: Emit signal for Dashboard propagation.
        """
        opacity = value / 100.0

        # -- Step 1: Global State (clears cache too) --
        ThemeManager.set_global_opacity(opacity)

        # -- Step 2: Visual Feedback --
        self.value_label.setText(f"{value}%")
        colors = self.theme.get_theme_colors()

        if value < 40:
            color = colors.get("danger", "#f43f5e")
        elif value < 70:
            color = colors.get("warning", "#f59e0b")
        else:
            color = colors.get("secondary", "#2dd4bf")

        self.value_label.setStyleSheet(
            f"color: {color}; font-weight: bold; font-family: 'Consolas'; font-size: 14px;"
        )

        # -- Step 3: Propagate to all cards via Dashboard --
        self.opacity_changed.emit(opacity)

    def get_opacity(self) -> float:
        """Returns current opacity as float 0.2-1.0"""
        return self.slider.value() / 100.0

    def refresh_styles(self):
        """Reloads styles from ThemeManager."""
        colors = self.theme.get_theme_colors()
        if not colors:
            return

        primary   = colors.get("primary",   "#3b82f6")
        secondary = colors.get("secondary", "#2dd4bf")
        bg_card   = colors.get("card_bg",   "rgba(15, 23, 42, 0.4)")

        self.label.setStyleSheet(f"""
            color: {primary};
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 1.5px;
            font-family: 'Inter', sans-serif;
        """)

        self.value_label.setStyleSheet(
            f"color: {secondary}; font-family: 'Consolas'; font-size: 14px;"
        )

        self.slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid {primary}33;
                height: 6px;
                background: {bg_card};
                margin: 2px 0;
                border-radius: 3px;
            }}
            QSlider::sub-page:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {primary}, stop:1 {secondary});
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {secondary}, stop:1 {primary});
                border: 1px solid {primary};
                width: 18px;
                height: 18px;
                margin: -7px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {secondary};
                border: 1px solid {secondary};
            }}
        """)

        self.setStyleSheet(f"""
            DimmerSlider {{
                background: {bg_card};
                border: 1px solid {primary}22;
                border-radius: 10px;
            }}
        """)
