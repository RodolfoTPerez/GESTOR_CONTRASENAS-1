# ══════════════════════════════════════════════════════════════
# EJEMPLO DE CONEXIÓN EN EL DASHBOARD
# Pega este patrón en tu clase principal del Dashboard
# ══════════════════════════════════════════════════════════════

from src.presentation.components.dimmer_slider import DimmerSlider
from src.presentation.components.vultrax_base_card import VultraxBaseCard


class TuDashboard(QWidget):  # o QMainWindow

    def _setup_dimmer(self):
        """Llamar esto en initUI / _setup_ui después de crear las tarjetas."""
        self.dimmer = DimmerSlider(self)

        # ── CONEXIÓN ÚNICA: el dimmer propaga a TODAS las tarjetas ──
        self.dimmer.opacity_changed.connect(self._on_dimmer_changed)

    def _on_dimmer_changed(self, opacity: float):
        """
        findChildren encuentra TODOS los VultraxBaseCard del dashboard,
        sin importar cuántos sean o en qué layout estén.
        No necesitas conectar cada tarjeta manualmente.
        """
        for card in self.findChildren(VultraxBaseCard):
            card.set_dimmer_opacity(opacity)


# ══════════════════════════════════════════════════════════════
# QUÉ HACE EL DIMMER EN CADA CAPA
# ══════════════════════════════════════════════════════════════
#
#  SLIDER MUEVE ──► ThemeManager.set_global_opacity(opacity)
#                        │
#                        ▼
#              ThemeManager.clear_cache()   ← limpia QSS cacheado
#                        │
#                        ▼
#         opacity_changed.emit(opacity)     ← señal al Dashboard
#                        │
#                        ▼
#         para cada tarjeta:
#           card.set_dimmer_opacity(opacity)
#               │
#               ├─► ThemeManager.set_global_opacity()  (ya seteado, OK)
#               └─► card.refresh_styles()
#                       │
#                       ├─► ThemeManager.clear_cache()
#                       ├─► style().unpolish(self)
#                       ├─► style().polish(self)   ← Qt relee QSS con nueva opacidad
#                       └─► self.update()
#
# ══════════════════════════════════════════════════════════════
# QUÉ SE VE AFECTADO POR EL DIMMER (por diseño del ThemeManager)
# ══════════════════════════════════════════════════════════════
#
#  ✅ AFECTADO (se dimmea):
#     @primary, @secondary, @accent, @danger, @warning, @success
#     @text, @text_dim, @info, @ai, @ai_sec
#     @primary_XX, @secondary_XX, etc. (todas las variantes)
#
#  ❌ NO AFECTADO (fondo estático, no se toca):
#     @bg, @bg_sec, @bg_dashboard_card, @card_bg
#     @shadow, @glow, @ghost_bg, @ghost_bg_light, @ghost_bg_dark
#     @white_XX, @black_XX, @ghost_white_XX, @ghost_black_XX
