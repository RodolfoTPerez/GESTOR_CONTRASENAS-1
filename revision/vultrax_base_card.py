from PyQt5.QtWidgets import QFrame, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from src.presentation.theme_manager import ThemeManager


class VultraxBaseCard(QFrame):
    """
    Standard Base Card for Vultrax Core Design System.
    Implements 12-column grid compatibility and token-based styling.

    DIMMER INTEGRATION:
    - set_dimmer_opacity(float) aplica la opacidad globalmente a TODOS los hijos
    - refresh_styles() regenera el QSS respetando ThemeManager._GLOBAL_OPACITY
    - El fondo (bg, card_bg) NO se ve afectado por diseño (ver ThemeManager.apply_tokens)
    """

    doubleClicked = pyqtSignal()
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("VultraxCard")
        self.setFrameShape(QFrame.NoFrame)

        # Standard layout for all cards
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 20, 24, 20)
        self.main_layout.setSpacing(16)

        # NOTE: Do NOT call refresh_styles here. Subclasses must call it
        # AFTER _setup_ui() to ensure all tactical indicators are defined.

    # ─────────────────────────────────────────────
    # DIMMER API — Punto de entrada único
    # ─────────────────────────────────────────────

    def set_dimmer_opacity(self, opacity: float):
        """
        Recibe el valor del DimmerSlider (0.2 – 1.0) y lo propaga al
        ThemeManager global. Luego regenera los estilos de ESTA tarjeta.

        Al usar ThemeManager._GLOBAL_OPACITY, TODOS los tokens @primary_XX,
        @secondary_XX, etc. quedan automáticamente modulados. Los fondos
        (bg, card_bg, ghost_bg) quedan intactos por diseño del ThemeManager.
        """
        # 1. Actualizar el estado global del ThemeManager
        ThemeManager.set_global_opacity(opacity)

        # 2. Regenerar estilos de esta tarjeta con la nueva opacidad
        self.refresh_styles()

    # ─────────────────────────────────────────────
    # STYLES
    # ─────────────────────────────────────────────

    def refresh_styles(self):
        """
        Regenera el QSS desde el ThemeManager respetando:
        - El tema activo (ThemeManager._GLOBAL_THEME)
        - La opacidad activa (ThemeManager._GLOBAL_OPACITY)

        Los fondos NO se ven afectados (background_keys en apply_tokens).
        Los colores semánticos (primary, text, danger…) SÍ se dimmean.
        """
        # Limpiar el cache para que apply_tokens regenere con la opacidad actual
        ThemeManager.clear_cache()

        # Repolish: Qt relee el QSS de la aplicación y lo aplica a este widget
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    # ─────────────────────────────────────────────
    # MOUSE EVENTS
    # ─────────────────────────────────────────────

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
