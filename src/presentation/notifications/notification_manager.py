from PyQt5.QtCore import QObject, QTimer, QPoint, Qt
from PyQt5.QtWidgets import QApplication
from src.presentation.widgets.toast import ToastNotification

class NotificationManager(QObject):
    """
    Gestor Global de Notificaciones (Toasts).
    Patrón Singleton para ser accesible desde cualquier punto.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NotificationManager, cls).__new__(cls)
            cls._instance.active_toasts = []
        return cls._instance

    def show_toast(self, parent_window, title, message, icon="ℹ️", accent_color="#06b6d4", duration=3000):
        """
        Crea y muestra un Toast en la esquina inferior derecha de la ventana padre.
        """
        # Limpieza de toasts cerrados
        # Limpieza de toasts cerrados (ROBUST FILTERING)
        active = []
        for t in self.active_toasts:
            try:
                if t.isVisible():
                    active.append(t)
            except RuntimeError:
                # Objeto C++ ya eliminado, lo ignoramos
                pass
        self.active_toasts = active
        
        # Crear Toast
        toast = ToastNotification(parent_window, title, message, icon, accent_color, duration)
        
        # Posicionamiento Inteligente (Stacking hacia arriba)
        # Margin from bottom-right
        margin_x = 20
        margin_y = 80
        spacing = 10
        
        # Calcular posición base (esquina inferior derecha del padre)
        if parent_window:
            geo = parent_window.geometry()
            base_x = geo.right() - toast.width() - margin_x
            base_y = geo.bottom() - toast.height() - margin_y
        else:
            # Fallback a pantalla
            screen = QApplication.primaryScreen().geometry()
            base_x = screen.right() - toast.width() - margin_x
            base_y = screen.bottom() - toast.height() - margin_y
            
        # Ajustar Y basado en cuantos toasts hay activos (stacking)
        stack_offset = len(self.active_toasts) * (toast.height() + spacing)
        final_y = base_y - stack_offset
        
        toast.move(base_x, final_y)
        toast.show_animated()
        
        self.active_toasts.append(toast)
        
        return toast

# Instancia Global
Notifications = NotificationManager()
