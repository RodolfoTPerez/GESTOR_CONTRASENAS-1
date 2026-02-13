from PyQt5.QtCore import QObject, QEvent, QTimer, Qt, QPoint, pyqtSignal
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QCursor
import logging

logger = logging.getLogger(__name__)

class GlobalInactivityWatcher(QObject):
    """
    Vigilante de actividad HÍBRIDO y SINGLETON.
    Garantiza que solo exista UN filtro en toda la aplicación para evitar RecursionErrors.
    """
    _instance = None
    _filtering = False
    
    timeout_changed = pyqtSignal(int)
    activity_detected = pyqtSignal()

    @classmethod
    def get_instance(cls, timeout_ms=300000, callback=None):
        if cls._instance is None:
            cls._instance = GlobalInactivityWatcher(timeout_ms, callback)
        else:
            if callback:
                cls._instance.callback = callback
            cls._instance.update_timeout(timeout_ms)
        return cls._instance

    def __init__(self, timeout_ms, callback_on_timeout):
        self.logger = logging.getLogger(__name__)
        # [NUCLEAR FIX] No pasar parent para evitar ciclos de eventos internos de Qt
        super().__init__()
        
        self.timeout_ms = timeout_ms
        self.callback = callback_on_timeout
        
        # Timer principal de inactividad
        self.timer = QTimer()
        self.timer.setInterval(self.timeout_ms)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._on_timeout)
        
        # [DEBUG]
        self.logger.debug(f"Initialized: {self.timeout_ms}ms")
        
        # Timer de Polling para Mouse (Anti-Recursion) - FRECUENCIA ALTA (Senior Protocol)
        self.poll_timer = QTimer()
        self.poll_timer.setInterval(250)
        self.poll_timer.timeout.connect(self._check_mouse_activity)
        
        self._last_mouse_pos = QCursor.pos()
        self._installed = False

    def start(self):
        """Inicia el monitoreo e instala el filtro global."""
        if not self._installed:
            app = QApplication.instance()
            if app:
                app.installEventFilter(self)
                self._installed = True
        
        self.timer.start()
        self.poll_timer.start()
        self.logger.info(f"Started | Timeout: {self.timeout_ms}ms")

    def stop(self):
        """Detiene el monitoreo."""
        # Nota: Normalmente no removemos el filtro global en el Singleton para evitar fricción,
        # solo detenemos los timers.
        self.timer.stop()
        self.poll_timer.stop()

    def update_timeout(self, new_ms):
        old_ms = self.timeout_ms
        self.timeout_ms = int(new_ms)
        self.logger.info(f"Update: {old_ms} -> {self.timeout_ms}ms (Forcing Restart)")
        
        # [NUCLEAR] Forzar reinicio siempre al actualizar timeout
        self.timer.start(self.timeout_ms)
        self.timeout_changed.emit(self.timeout_ms)

    def _on_timeout(self):
        self.timer.stop()
        self.poll_timer.stop()
        if self.callback:
            try:
                cb_name = self.callback.__name__ if hasattr(self.callback, '__name__') else str(self.callback)
                self.logger.info(f"TIMEOUT REACHED. Executing callback: {cb_name}")
                self.callback()
            except Exception as e:
                self.logger.error(f"Callback failed: {e}")

    def _check_mouse_activity(self):
        """Consulta la posición del mouse sin generar eventos."""
        if GlobalInactivityWatcher._filtering: return
        try:
            current_pos = QCursor.pos()
            if current_pos != self._last_mouse_pos:
                self._last_mouse_pos = current_pos
                logger.debug("Activity Detected (Polling)")
                self.reset_timer()
        except: pass

    def eventFilter(self, obj, event):
        """Filtro global para Teclado, Clicks y Movimiento."""
        # [RECURSION GUARD]
        if GlobalInactivityWatcher._filtering:
            return False
            
        try:
            # Solo procesar si el watcher está activo
            if not self.timer.isActive():
                return False

            GlobalInactivityWatcher._filtering = True
            
            etype = event.type()
            # AGGRESSIVE TRACKING: Capture everything including movement
            if etype in (QEvent.KeyPress, QEvent.MouseMove, QEvent.MouseButtonPress, QEvent.MouseButtonDblClick, QEvent.Wheel, QEvent.TouchBegin):
                self.reset_timer()
        except:
            pass
        finally:
            GlobalInactivityWatcher._filtering = False
            
        return False # Propagar siempre

    def reset_timer(self):
        """Reinicia el cronómetro de inactividad."""
        try:
            if self.timer.isActive():
                logger.debug(f"Resetting timer ({self.timeout_ms}ms)")
                self.timer.start(self.timeout_ms)
                try: self.activity_detected.emit()
                except: pass
        except:
            pass
