from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QApplication
from PyQt5.QtCore import Qt, pyqtSignal
from src.presentation.theme_manager import ThemeManager


class DimmerSlider(QWidget):
    """
    Tactical Dimmer Slider for granular opacity control.

    FLUJO CORRECTO:
    1. Usuario mueve el slider
    2. _on_value_changed() llama ThemeManager.set_global_opacity()
       → Esto limpia el cache del ThemeManager automáticamente
    3. Se emite opacity_changed(float) para que el Dashboard
       llame set_dimmer_opacity() en TODAS las tarjetas
    4. Cada tarjeta llama refresh_styles() → relee QSS con nueva opacidad

    IMPORTANTE: El Dashboard debe conectar la señal así:
        self.dimmer.opacity_changed.connect(self._on_dimmer_changed)

        def _on_dimmer_changed(self, opacity):
            for card in self.findChildren(VultraxBaseCard):
                card.set_dimmer_opacity(opacity)
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
        # Inicializar desde el estado global actual para sincronía
        self.slider.setValue(int(ThemeManager._GLOBAL_OPACITY * 100))
        self.slider.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.slider)

        self.value_label = QLabel(f"{int(ThemeManager._GLOBAL_OPACITY * 100)}%")
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)

    def _on_value_changed(self, value: int):
        """
        Paso 1: Actualizar el estado global PRIMERO.
        Paso 2: Dar feedback visual en el slider.
        Paso 3: Emitir señal para que el Dashboard propague a las tarjetas.
        """
        opacity = value / 100.0

        # ── Paso 1: Estado global (también limpia el cache) ──
        ThemeManager.set_global_opacity(opacity)

        # ── Paso 2: Feedback visual del label ──
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

        # ── Paso 3: Propagar a todas las tarjetas vía Dashboard ──
        self.opacity_changed.emit(opacity)

    def get_opacity(self) -> float:
        """Retorna la opacidad actual como float 0.2–1.0"""
        return self.slider.value() / 100.0

    def refresh_styles(self):
        """Recarga estilos desde el ThemeManager."""
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
