from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QEventLoop
from src.domain.messages import MESSAGES
from src.presentation.theme_manager import ThemeManager
from src.presentation.notifications.notification_manager import Notifications
from src.presentation.widgets.glass_overlay import GlassOverlay

class PremiumMessage:
    """Helper para mostrar diálogos de alerta con estética premium y temática."""
    
    # Mantenemos _create_base por si algún código legado lo llama directo, 
    # aunque idealmente debería ser privado. Lo redirigiremos a Toasts si es posible
    # o mantendremos el fallback a QMessageBox si `type` es complejo.
    
    @staticmethod
    def _create_base(parent, title, text, icon_emoji, accent_key="primary"):
        theme = ThemeManager()
        colors = theme.get_theme_colors()
        accent = colors.get(accent_key, "#06b6d4")
        Notifications.show_toast(parent, title, text, icon_emoji, accent)
        
        class DummyMsg:
            def exec_(self): pass
            def setStandardButtons(self, _): pass
            def button(self, _): 
                class B: 
                    def setText(self, _): pass
                return B()
        return DummyMsg()

    @staticmethod
    def warning(parent, title, text, duration=8000):
        theme = ThemeManager()
        colors = theme.get_theme_colors()
        col = colors.get("warning", "#f59e0b")
        Notifications.show_toast(parent, title, text, "⚠️", col, duration)

    @staticmethod
    def info(parent, title, text, duration=6000):
        theme = ThemeManager()
        colors = theme.get_theme_colors()
        col = colors.get("info", colors.get("primary", "#3b82f6"))
        Notifications.show_toast(parent, title, text, "ℹ️", col, duration)

    information = info

    @staticmethod
    def success(parent, title, text, duration=6000):
        theme = ThemeManager()
        colors = theme.get_theme_colors()
        col = colors.get("success", "#10b981")
        Notifications.show_toast(parent, title, text, "✅", col, duration)

    @staticmethod
    def error(parent, title, text, duration=10000):
        if not text:
            text = "Se ha producido un error inesperado sin mensaje detallado."
        theme = ThemeManager()
        colors = theme.get_theme_colors()
        col = colors.get("danger", "#ef4444")
        Notifications.show_toast(parent, title, text, "❌", col, duration)

    # Alias for critical -> error (Backward compatibility)
    critical = error

    @staticmethod
    def question(parent, title, text):
        """
        Muestra un overlay de cristal bloqueante (Modal) y espera respuesta.
        Usa QEventLoop para mantener la sincronicidad del API original.
        """
        if not parent:
            # Fallback a QMessageBox si no hay padre para el overlay
            msg = QMessageBox()
            msg.setWindowTitle(title)
            msg.setText(text)
            msg.setIcon(QMessageBox.Question)
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            return msg.exec_() == QMessageBox.Yes

        # Crear Overlay
        overlay = GlassOverlay(parent, title, text)
        
        # Loop local para esperar la señal (Sincronicidad)
        loop = QEventLoop()
        result = [False]
        
        def on_answer(ans):
            result[0] = ans
            loop.quit()
            
        overlay.answer_selected.connect(on_answer)
        overlay.show_modal()
        
        # Bloquear ejecución aquí hasta que el usuario responda
        loop.exec_()
        
        return result[0]
