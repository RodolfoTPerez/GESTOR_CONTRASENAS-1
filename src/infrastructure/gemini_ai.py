try:
    import google.genai as genai  # nuevo cliente (recomendado)
except Exception:
    try:
        import google.generativeai as genai  # compatibilidad retro
    except Exception:
        genai = None

from config.config import GEMINI_API_KEY
import logging

logger = logging.getLogger(__name__)

class GeminiAI:
    """
    Motor de Inteligencia Artificial Avanzada basado en Google Gemini.
    Proporciona razonamiento de seguridad, chat interactivo y análisis predictivo.
    """
    def __init__(self, api_key=None):
        self.api_key = api_key or GEMINI_API_KEY
        self.enabled = False
        self.model = None
        self.client = None
        self.model_id = None
        if self.api_key:
            self.configure(self.api_key)

    def configure(self, api_key):
        """Configura o reconfigura el motor de Gemini con una nueva API Key."""
        if not api_key:
            self.enabled = False
            return
        self.api_key = api_key
        try:
            if genai is None:
                raise RuntimeError("Cliente de Gemini no disponible (paquete google.genai / google.generativeai no encontrado)")

            # Preferir usar configure si existe en el SDK
            if hasattr(genai, 'configure'):
                try:
                    genai.configure(api_key=self.api_key)
                except Exception:
                    pass

            # Intentar crear objeto de modelo o cliente según el SDK
            if hasattr(genai, 'GenerativeModel'):
                try:
                    self.model = genai.GenerativeModel('gemini-1.5-flash')
                    self.model_id = 'gemini-1.5-flash'
                except Exception:
                    client_cls = getattr(genai, 'Client', None)
                    if client_cls:
                        try:
                            self.client = client_cls(api_key=self.api_key)
                        except Exception:
                            self.client = None
            else:
                client_cls = getattr(genai, 'Client', None)
                if client_cls:
                    try:
                        self.client = client_cls(api_key=self.api_key)
                    except Exception:
                        self.client = None

            # Detectar modelo disponible si es client.models
            if self.client and hasattr(self.client, 'models'):
                try:
                    models = self.client.models.list()
                    # Preferir gemini-pro, luego gemini-1.0-pro, luego el primero
                    prefer = ['gemini-pro', 'gemini-1.0-pro', 'gemini-1.5-flash']
                    found = None
                    for p in prefer:
                        for m in models:
                            if hasattr(m, 'name') and p in m.name:
                                found = m.name
                                break
                        if found:
                            break
                    if not found and models:
                        found = getattr(models[0], 'name', None)
                    if found:
                        self.model_id = found
                        logger.info(f"GeminiAI: Model detected: {self.model_id}")
                except Exception as e:
                    logger.error(f"GeminiAI: Error detecting models: {e}")

            if self.model or self.client:
                self.enabled = True
                logger.info('Gemini AI: Client configured successfully.')
            else:
                raise RuntimeError('No se pudo inicializar cliente/modelo Gemini con el SDK instalado.')
        except Exception as e:
            self.enabled = False
            logger.error(f'Error configuring Gemini AI: {e}')

    def ask(self, prompt, context=""):
        """Envía una consulta a Gemini con un contexto opcional."""
        if not self.enabled:
            return "El motor Gemini AI no está configurado (falta API Key)."
        try:
            full_prompt = f"Contexto de Seguridad: {context}\n\nPregunta: {prompt}\n\ngenera una respuesta profesional, concisa y enfocada en ciberseguridad para un usuario de gestor de contraseñas."

            # --- AUDIT LOG (Transparency) ---
            logger.debug(f"AI AUDIT - Prompt sent to Gemini: {full_prompt}")

            # 1) Si disponemos de un model con métodos modernos
            if self.model is not None:
                if hasattr(self.model, 'generate_content'):
                    response = self.model.generate_content(full_prompt)
                    return getattr(response, 'text', None) or str(response)
                if hasattr(self.model, 'generate'):
                    response = self.model.generate(full_prompt)
                    return getattr(response, 'text', None) or str(response)

            # 2) Si disponemos de un client genérico, intentar métodos comunes
            if self.client is not None:
                # SDKs like google-genai exponen `client.models.generate_content`
                try:
                    models = getattr(self.client, 'models', None)
                    if models and hasattr(models, 'generate_content') and self.model_id:
                        try:
                            resp = models.generate_content(model=self.model_id, contents=full_prompt)
                            # Extraer texto de la respuesta Gemini (google-genai)
                            if hasattr(resp, 'candidates') and resp.candidates:
                                out = []
                                for c in resp.candidates:
                                    # google-genai: c.content.parts[0].text
                                    content = getattr(c, 'content', None)
                                    if content and hasattr(content, 'parts') and content.parts:
                                        part = content.parts[0]
                                        text = getattr(part, 'text', None)
                                        if text:
                                            out.append(text)
                                if out:
                                    return '\n'.join(out)
                            # Fallback: intentar .text o str
                            return getattr(resp, 'text', None) or str(resp)
                        except Exception as e:
                            return f"Error Gemini: {e}"
                except Exception as e:
                    return f"Error Gemini: {e}"

                for method in ('generate_text', 'generate', 'predict', 'text_generate'):
                    fn = getattr(self.client, method, None)
                    if callable(fn):
                        try:
                            resp = fn(full_prompt)
                            return getattr(resp, 'text', None) or str(resp)
                        except Exception:
                            continue

            return "Error al generar respuesta de IA: cliente no inicializado o método no soportado en este SDK."
        except Exception as e:
            return f"Error al generar respuesta de IA: {str(e)}"

    def analyze_vulnerabilities(self, report_data):
        """Usa Gemini para razonar sobre los hallazgos del motor heurístico."""
        if not self.enabled:
            return "IA Avanzada no disponible."
        
        if isinstance(report_data, dict):
            strat = report_data.get("strategic_context", {})
            integrity = report_data.get("system_integrity", {})
            
            # --- MASTER HEALTH PROMPT (CISO LEVEL) ---
            prompt = f"""Actúa como un CISO (Chief Information Security Officer) de alto nivel. 
Analiza la salud TOTAL de esta infraestructura de seguridad con los siguientes datos:

1. MÉTRICAS DE BÓVEDA:
- Puntuación: {report_data.get('score')}/100 ({report_data.get('status')})
- Total registros: {report_data.get('stats', {}).get('total')} (Analizados {report_data.get('stats', {}).get('analyzed')})
- Reutilizadas: {report_data.get('stats', {}).get('reused')} | Débiles: {report_data.get('stats', {}).get('weak')}

2. CONTEXTO ESTRUCTURAL:
- Servicios Críticos Expuestos: {strat.get('high_impact_services', [])}
- Antigüedad Promedio: {strat.get('average_age_days')} días (Máxima: {strat.get('oldest_record_days')} días)
- Déficit de Composición: {strat.get('composition_deficits', {})}

3. INTEGRIDAD DEL SISTEMA:
- Protección de Hardware (HWID): {'ACTIVA' if integrity.get('hwid_enforced') else 'INACTIVA'}
- Sincronización Nube-Local: {integrity.get('sync_status', 'N/A')}
- Auditoría: {report_data.get('audit_summary', 'Sin anomalías recientes')}

4. HALLAZGOS ESPECÍFICOS:
{chr(10).join([f'- {f.get("title")}: {f.get("desc")}' for f in report_data.get('findings', [])])}

Dame un diagnóstico ejecutivo breve y un plan maestro de 3 puntos clave para mejorar la postura de seguridad de la organización."""
        else:
            prompt = f"Analiza estos hallazgos técnicos y dame un resumen estratégico:\n{report_data}"

        return self.ask(prompt, context="Eres un experto en ciberseguridad analizando una bóveda personal.")

class ChatGPTAI:
    """Motor IA basado en OpenAI ChatGPT utilizando peticiones directas API."""
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.enabled = True if api_key else False
        self.url = "https://api.openai.com/v1/chat/completions"
    
    def configure(self, api_key):
        self.api_key = api_key
        self.enabled = True if api_key else False

    def ask(self, prompt, context=""):
        if not self.enabled: return "ChatGPT no configurado (Falta API Key)."
        import json, urllib.request
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            data = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": context or "Eres un experto en ciberseguridad."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
            
            # --- AUDIT LOG (Transparency) ---
            logger.debug(f"AI AUDIT - Prompt sent to ChatGPT: SYSTEM: {context or 'Cybersecurity Expert'} USER: {prompt}")

            req = urllib.request.Request(self.url, data=json.dumps(data).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"Error API ChatGPT: {str(e)}"

    def analyze_vulnerabilities(self, report_data):
        if not self.enabled: return "ChatGPT no disponible."
        
        # Sincronizado con el Prompt Maestro de Gemini
        if isinstance(report_data, dict):
            strat = report_data.get("strategic_context", {})
            integrity = report_data.get("system_integrity", {})
            
            prompt = f"""Actúa como un CISO Corporativo. Analiza la salud global de este ecosistema:
1. MÉTRICAS: Score {report_data.get('score')}, Status {report_data.get('status')}.
2. ESTRUCTURA: Critical Services {strat.get('high_impact_services')}. Avg Age {strat.get('average_age_days')} days.
3. INTEGRIDAD: HWID {'Activo' if integrity.get('hwid_enforced') else 'No detected'}, Sync {integrity.get('sync_status')}.
4. HALLAZGOS:
{chr(10).join([f'- {f.get("title")}: {f.get("desc")}' for f in report_data.get('findings', [])])}

Dame un diagnóstico ejecutivo y 3 pasos de mitigación."""
        else:
            prompt = f"Analiza estos datos de auditoría y dame 3 consejos críticos:\n{report_data}"
            
        return self.ask(prompt)

class ClaudeAI:
    """Motor IA basado en Anthropic Claude utilizando peticiones directas API."""
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.enabled = True if api_key else False
        self.url = "https://api.anthropic.com/v1/messages"
    
    def configure(self, api_key):
        self.api_key = api_key
        self.enabled = True if api_key else False

    def ask(self, prompt, context=""):
        if not self.enabled: return "Claude no configurado (Falta API Key)."
        import json, urllib.request
        
        try:
            headers = {
                "content-type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
            data = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1024,
                "system": context or "Eres un experto en ciberseguridad.",
                "messages": [{"role": "user", "content": prompt}]
            }
            req = urllib.request.Request(self.url, data=json.dumps(data).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data["content"][0]["text"].strip()
        except Exception as e:
            return f"Error API Claude: {str(e)}"

    def analyze_vulnerabilities(self, report_data):
        if not self.enabled: return "Claude no disponible."
        return self.ask("Analiza la salud de esta bóveda y dame 3 consejos de experto.")
