import os
from PyQt5.QtCore import QObject, pyqtSignal
import logging

class ThemeManager(QObject):
    """
    Manages the application's visual themes.
    Loads QSS files and applies them to widgets or the entire application.
    """
    
    # Global state to sync widgets without passing settings everywhere
    _GLOBAL_THEME = None
    
    # [CONFIG] Constante para QSettings
    APP_ID = "VultraxCore"

    # Signals for reactivity
    theme_changed = pyqtSignal(str)

    # Predefined color palettes for themes
    THEMES = {
        "tactical_dark": {
            "name": "Tactical Dark (Default)",
            "bg": "#0a0f1d",
            "bg_sec": "#161d31",
            "primary": "#3b82f6",
            "secondary": "#2dd4bf",
            "accent": "#6366f1",
            "text": "#f1f5f9",
            "text_dim": "#94a3b8",
            "danger": "#f43f5e",
            "warning": "#f59e0b",
            "success": "#10b981",
            "border": "rgba(59, 130, 246, 0.15)",
            "bg_dashboard_card": "#0f172a",
            "info": "#3b82f6",
            "ai": "#8b5cf6",
            "ai_sec": "#a78bfa",
            "text_on_primary": "#ffffff",
            # Structural Tokens (Standardized)
            "border-radius-main": "12px",
            "border-width-main": "1px",
            "font-family-main": "'Inter', 'Segoe UI', sans-serif",
            # VULTRAX TOKENS
            "color-bg-primary": "#0a0f1d",
            "color-bg-secondary": "#161d31",
            "color-bg-tertiary": "#0f172a",
            "color-text-primary": "#f1f5f9",
            "color-text-secondary": "#94a3b8",
            "color-danger": "#f43f5e",
            "color-warning": "#f59e0b",
            "color-success": "#10b981",
            "color-accent": "#6366f1",
            "color-primary": "#3b82f6",
            "color-border": "rgba(59, 130, 246, 0.15)",
            "shadow": "rgba(0, 0, 0, 0.5)",
            "glow": "rgba(59, 130, 246, 0.2)",
            "card_bg": "#0f172a"
        },
        "phantom_glass": {
            "name": "Phantom Glass (Evolved)",
            "bg": "#1A202C",
            "bg_sec": "rgba(45, 55, 72, 0.7)",
            "primary": "#81E6D9",
            "secondary": "#4299E1",
            "accent": "#90CDF4",
            "text": "#E2E8F0",
            "text_dim": "#A0AEC0",
            "danger": "#F56565",
            "warning": "#ED8936",
            "success": "#48BB78",
            "border": "rgba(255, 255, 255, 0.1)",
            "bg_dashboard_card": "rgba(45, 55, 72, 0.4)",
            "info": "#4299E1",
            "ai": "#9F7AEA",
            "ai_sec": "#B794F4",
            "text_on_primary": "#1A202C",
            # Structural Tokens
            "border-radius-main": "12px",
            "border-width-main": "1px",
            "font-family-main": "'Inter', sans-serif",
            "shadow": "rgba(0, 0, 0, 0.3)",
            "glow": "rgba(129, 230, 217, 0.15)",
            "card_bg": "rgba(45, 55, 72, 0.4)"
        },
        "bunker_ops": {
            "name": "Bunker Ops (Neo-Brutalism)",
            "bg": "#F0F0F0",
            "bg_sec": "#FFFFFF",
            "primary": "#FFDE59",
            "secondary": "#000000",
            "accent": "#FF5757",
            "text": "#000000",
            "text_dim": "#4A4A4A",
            "danger": "#FF5757",
            "warning": "#FFDE59",
            "success": "#000000",
            "border": "#000000",
            "bg_dashboard_card": "#FFFFFF",
            "info": "#000000",
            "ai": "#000000",
            "ai_sec": "#4A4A4A",
            "text_on_primary": "#000000",
            # Structural Tokens
            "border-radius-main": "0px",
            "border-width-main": "2px",
            "font-family-main": "'Consolas', 'Courier New', monospace",
            "shadow": "rgba(0, 0, 0, 0.15)",
            "glow": "rgba(0, 0, 0, 0)",
            "card_bg": "#FFFFFF"
        },
        "obsidian_flow": {
            "name": "Obsidian Flow (Deep Space)",
            "bg": "#050505",
            "bg_sec": "#111111",
            "primary": "#7928CA",
            "secondary": "#FF0080",
            "accent": "#7928CA",
            "text": "#EDEDED",
            "text_dim": "#888888",
            "danger": "#FF0000",
            "warning": "#F59E0B",
            "success": "#00FFA3",
            "border": "#333333",
            "bg_dashboard_card": "#111111",
            "info": "#0070F3",
            "ai": "#7928CA",
            "ai_sec": "#FF0080",
            "text_on_primary": "#FFFFFF",
            # Structural Tokens
            "border-radius-main": "8px",
            "border-width-main": "1px",
            "font-family-main": "'Inter', sans-serif",
            "shadow": "rgba(0, 0, 0, 0.7)",
            "glow": "rgba(121, 40, 202, 0.25)",
            "card_bg": "#111111"
        },
        "neon_overdrive": {
            "name": "Neon Overdrive (Spectacular)",
            "bg": "#050505",
            "bg_sec": "#121212",
            "primary": "#f43f5e",
            "secondary": "#fb7185",
            "accent": "#d946ef",
            "text": "#ffffff",
            "text_dim": "#71717a",
            "danger": "#ff0000",
            "warning": "#fbbf24",
            "success": "#22c55e",
            "border": "rgba(244, 63, 94, 0.2)",
            "bg_dashboard_card": "#0a0a0a",
            "info": "#fb7185",
            "ai": "#d946ef",
            "ai_sec": "#f43f5e",
            "text_on_primary": "#ffffff",
            # Structural Tokens
            "border-radius-main": "10px",
            "border-width-main": "1px",
            "font-family-main": "'Inter', sans-serif",
            "shadow": "rgba(244, 63, 94, 0.4)",
            "glow": "rgba(244, 63, 94, 0.2)",
            "card_bg": "#0a0a0a"
        },
        "saas_commercial": {
            "name": "SaaS Commercial (Final)",
            "bg": "#020617",
            "bg_sec": "#071226",
            "primary": "#3b82f6",
            "secondary": "#00ffa3",
            "accent": "#6366f1",
            "text": "#e6edf3",
            "text_dim": "#94a3b8",
            "danger": "#ef4444",
            "warning": "#f59e0b",
            "success": "#00ffa3",
            "border": "rgba(255, 255, 255, 0.06)",
            "bg_dashboard_card": "#0b1730",
            "info": "#3b82f6",
            "ai": "#8b5cf6",
            "ai_sec": "#a78bfa",
            "text_on_primary": "#ffffff",
            # Structural Tokens
            "border-radius-main": "8px",
            "border-width-main": "1px",
            "font-family-main": "'Inter', sans-serif",
            "shadow": "rgba(0, 0, 0, 0.3)",
            "glow": "rgba(59, 130, 246, 0.1)",
            "card_bg": "#0b1730"
        }
    }

    def __init__(self, parent_app=None):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.app = parent_app
        
        # Load active theme from settings FIRST if global not set
        if not ThemeManager._GLOBAL_THEME:
            from PyQt5.QtCore import QSettings
            settings = QSettings(ThemeManager.APP_ID, "VultraxCore_Global")
            ThemeManager._GLOBAL_THEME = settings.value("theme_active", "saas_commercial")
            
        self.current_theme = ThemeManager._GLOBAL_THEME

    def get_theme_colors(self, theme_id=None):
        # Always prefer global unless specifically requested
        tid = theme_id or ThemeManager._GLOBAL_THEME or self.current_theme
        return self.THEMES.get(tid)

    @classmethod
    def clear_cache(cls):
        """Clears the processed stylesheet cache to force reload from disk."""
        cls._STYLESHEET_CACHE = {}
        logging.getLogger(__name__).info("ThemeManager: Stylesheet cache cleared.")

    _applying_theme = False

    def apply_app_theme(self, app):
        """Applies both base and dashboard styles to the entire application efficiently."""
        if ThemeManager._applying_theme:
            return
        
        # [SENIOR FIX] Clear cache before applying to ensure we read latest from disk
        self.clear_cache()
        
        ThemeManager._applying_theme = True
        try:
            base_qss = self.load_stylesheet("base")
            dash_qss = self.load_stylesheet("dashboard")
            dialog_qss = self.load_stylesheet("dialogs")
            full_qss = f"{base_qss}\n{dash_qss}\n{dialog_qss}"
            
            app.setStyleSheet(full_qss)
            
            # Re-polish the application and the active window to ensure global changes propagate
            app.style().unpolish(app)
            app.style().polish(app)
            
            # [SENIOR REFINEMENT] Polish the active window to force children to re-read stylesheet
            active_window = app.activeWindow()
            if active_window:
                active_window.style().unpolish(active_window)
                active_window.style().polish(active_window)
                active_window.update()
            
            logging.getLogger(__name__).info("ThemeManager: Global theme applied successfully.")
        except Exception as e:
            logging.getLogger(__name__).error(f"ThemeManager: Critical error applying theme: {e}")
        finally:
            ThemeManager._applying_theme = False

    # [OPTIMIZATION] Cache de hojas de estilo procesadas para evitar lag en I/O
    _STYLESHEET_CACHE = {}

    def apply_tokens(self, content, theme_id=None):
        """Replaces @tokens in a string with current theme colors."""
        theme_id = theme_id or self.current_theme
        colors = self.get_theme_colors(theme_id).copy()
        
        # --- GHOST COLOR NUCLEAR GENERATOR ---
        ghost_colors = {}
        # Base Ghost Colors
        bg_color = colors.get("bg", "#0f172a")
        ghost_colors["ghost_bg"] = colors.get("card_bg", "rgba(15, 23, 42, 0.35)")
        ghost_colors["ghost_bg_light"] = "rgba(255,255,255,0.05)"
        ghost_colors["ghost_bg_dark"] = "rgba(0,0,0,0.6)"
        ghost_colors["ghost_border"] = colors.get("border", "rgba(255,255,255,0.1)")
        
        # Semantic Opacity Matrix
        opacity_variants = {
            "08": 0.08, "10": 0.10, "15": 0.15, "20": 0.20, "25": 0.25, 
            "30": 0.30, "35": 0.35, "40": 0.40, "45": 0.45, "55": 0.55, 
            "65": 0.65, "75": 0.75, "85": 0.85, "90": 0.90, "95": 0.95
        }
        
        core_semantic_keys = ["primary", "secondary", "accent", "danger", "warning", "success", "info", "ai", "ai_sec", "text", "text_dim"]
        
        for k in core_semantic_keys:
            if k in colors:
                val = colors[k]
                r, g, b = 255, 255, 255 # Default
                if val.startswith("#"):
                    h = val.lstrip('#')
                    if len(h) == 6:
                        r, g, b = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
                elif val.startswith("rgba"):
                    try:
                        parts = val.replace("rgba(", "").replace(")", "").split(",")
                        r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
                    except: pass
                
                alpha = 0.45 if k in ["danger", "warning"] else 0.25
                ghost_colors[f"ghost_{k}"] = f"rgba({r}, {g}, {b}, {alpha})"
                
                # Base variants (e.g. @primary_20)
                for suffix, alpha_val in opacity_variants.items():
                    ghost_colors[f"ghost_{k}_{suffix}"] = f"rgba({r}, {g}, {b}, {alpha_val})"
                    ghost_colors[f"{k}_{suffix}"] = f"rgba({r}, {g}, {b}, {alpha_val})"
        
        for suffix, alpha_val in opacity_variants.items():
            ghost_colors[f"ghost_white_{suffix}"] = f"rgba(255, 255, 255, {alpha_val})"
            ghost_colors[f"ghost_black_{suffix}"] = f"rgba(0, 0, 0, {alpha_val})"
            ghost_colors[f"white_{suffix}"] = f"rgba(255, 255, 255, {alpha_val})"
            ghost_colors[f"black_{suffix}"] = f"rgba(0, 0, 0, {alpha_val})"

        colors.update(ghost_colors)
        
        # [SENIOR FIX] Use regex to avoid partial token replacement (e.g. @primary vs @primary_20)
        import re
        def replace_match(match):
            key = match.group(1)
            return colors.get(key, f"@{key}")
            
        return re.sub(r"@([\w-]+)", replace_match, content)

    def load_stylesheet(self, component_name, theme_id=None):
        """Loads a QSS file and replaces variables with theme colors (Cached)."""
        theme_id = theme_id or self.current_theme
        
        cache_key = (component_name, theme_id)
        if cache_key in ThemeManager._STYLESHEET_CACHE:
            return ThemeManager._STYLESHEET_CACHE[cache_key]
            
        base_dir = os.path.dirname(__file__)
        file_path = os.path.join(base_dir, "styles", f"{component_name}.qss")
        
        if not os.path.exists(file_path):
            return ""

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Process tokens using the centralized method
            content = self.apply_tokens(content, theme_id)
            
            ThemeManager._STYLESHEET_CACHE[cache_key] = content
            return content
        except Exception as e:
            self.logger.error(f"Could not load stylesheet {component_name}: {e}")
            return ""

    def set_theme(self, theme_id):
        if theme_id in self.THEMES:
            self.current_theme = theme_id
            ThemeManager._GLOBAL_THEME = theme_id
            self.theme_changed.emit(theme_id)
            return True
        return False
