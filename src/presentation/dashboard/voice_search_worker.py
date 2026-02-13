import logging
import speech_recognition as sr
from PyQt5.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

class VoiceSearchWorker(QThread):
    """
    Trabajador asíncrono para captura de voz y conversión a texto.
    """
    result_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    listening_started = pyqtSignal()
    listening_finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        self.is_running = False

    def run(self):
        self.is_running = True
        try:
            with self.mic as source:
                # OPTIMIZACIÓN: Reducir tiempo de ajuste de ruido (0.3s es suficiente en interiores)
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                
                # OPTIMIZACIÓN: Umbral de energía dinámica
                self.recognizer.dynamic_energy_threshold = True
                
                # OPTIMIZACIÓN: Reducir el tiempo de silencio necesario para considerar fin de frase (default is 0.8s)
                # 0.5s hace que se sienta mucho más instantáneo
                self.recognizer.pause_threshold = 0.5 
                
                self.listening_started.emit()
                
                logger.info("VoiceSearch: Listening...")
                # Reducir timeouts para no dejar al usuario esperando si no habla
                audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=4)
                
                self.listening_finished.emit()
                logger.info("VoiceSearch: Processing audio (Google API)...")
                
                # Intentar reconocer el audio (Google es el default y gratuito)
                # Se puede configurar el lenguaje aquí (es-ES para español)
                text = self.recognizer.recognize_google(audio, language="es-ES")
                
                logger.info(f"VoiceSearch: Recognized: {text}")
                
                # Post-procesamiento básico: "busca correo de rodolfo" -> "rodolfo"
                processed_text = self._parse_command(text)
                self.result_ready.emit(processed_text)
                
        except sr.WaitTimeoutError:
            logger.warning("VoiceSearch: Timeout waiting for phrase")
            self.error_occurred.emit("Tiempo de espera agotado")
        except sr.UnknownValueError:
            logger.warning("VoiceSearch: Could not understand audio")
            self.error_occurred.emit("No se pudo entender el audio")
        except sr.RequestError as e:
            logger.error(f"VoiceSearch: Could not request results; {e}")
            self.error_occurred.emit("Error de conexión con el servicio de voz")
        except Exception as e:
            logger.error(f"VoiceSearch: Unexpected error; {e}")
            self.error_occurred.emit(f"Error inesperado: {str(e)}")
        finally:
            self.is_running = False
            self.listening_finished.emit()

    def _parse_command(self, text):
        """
        Lógica simple para extraer la intención de búsqueda.
        Ejemplo: "busca correo de rodolfo@gmail.com" -> "rodolfo@gmail.com"
        """
        text = text.lower()
        prefixes = [
            "busca correo de",
            "buscar correo de",
            "busca",
            "buscar",
            "encuentra",
            "encontrar"
        ]
        
        for prefix in prefixes:
            if text.startswith(prefix):
                return text.replace(prefix, "").strip()
        
        return text.strip()
