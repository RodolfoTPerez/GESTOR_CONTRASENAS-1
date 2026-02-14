import re
import math
import difflib
from datetime import datetime
from collections import Counter
import logging

logger = logging.getLogger(__name__)

try:
    from src.infrastructure.gemini_ai import GeminiAI, ChatGPTAI, ClaudeAI
except Exception:
    # Stubs básicos en caso de error de carga
    class GeminiAI:
        def __init__(self, api_key=None): self.enabled = False
        def configure(self, key): pass
        def analyze_vulnerabilities(self, data): return "Gemini no disponible."
    class ChatGPTAI:
        def __init__(self, api_key=None): self.enabled = False
        def configure(self, key): pass
        def analyze_vulnerabilities(self, data): return "ChatGPT no disponible."
    class ClaudeAI:
        def __init__(self, api_key=None): self.enabled = False
        def configure(self, key): pass
        def analyze_vulnerabilities(self, data): return "Claude no disponible."

class GuardianAI:
    def __init__(self, engine="Google Gemini", api_key=None):
        self.engine = engine
        self.api_key = api_key or ""
        
        # Inicializar todos los motores
        self.gemini = GeminiAI(api_key=self.api_key if "Gemini" in self.engine else None)
        self.chatgpt = ChatGPTAI(api_key=self.api_key if "ChatGPT" in self.engine else None)
        self.claude = ClaudeAI(api_key=self.api_key if "Claude" in self.engine else None)
        
        # Patrones comunes de contraseñas débiles
        self.weak_patterns = [
            r'^[0-9]+$',                  # Solo números
            r'^[a-zA-Z]+$',               # Solo letras
            r'123', 'qwerty', 'password', # Secuencias comunes
            r'abcd', 'admin', 'root'
        ]
        
        # Palabras clave para Radio de Impacto
        self.impact_keywords = {
            'CRITICAL': ['gmail', 'outlook', 'hotmail', 'proton', 'icloud', 'yahoo', 'aws', 'azure', 'google cloud', 'root', 'admin'],
            'FINANCIAL': ['banco', 'bank', 'bbva', 'santander', 'paypal', 'stripe', 'wallet', 'binance', 'coinbase', 'visa', 'mastercard'],
            'SOCIAL': ['facebook', 'twitter', 'x.com', 'instagram', 'linkedin', 'slack', 'discord', 'whatsapp', 'telegram']
        }

    def configure_engine(self, engine_name, api_key):
        """Alterna el motor activo y le asigna su llave."""
        logger.info(f"GuardianAI: Switching engine to '{engine_name}'...")
        self.engine = engine_name
        self.api_key = api_key
        
        # Desactivar todos primero para evitar fugas de lógica
        self.gemini.enabled = False
        self.chatgpt.enabled = False
        self.claude.enabled = False
        
        if "Gemini" in engine_name:
            self.gemini.configure(api_key)
        elif "ChatGPT" in engine_name:
            self.chatgpt.configure(api_key)
        elif "Claude" in engine_name:
            self.claude.configure(api_key)
            
    def _get_active_engine(self):
        """Retorna la instancia del motor que coincide con la configuración actual."""
        if "Gemini" in self.engine: return self.gemini
        if "ChatGPT" in self.engine: return self.chatgpt
        if "Claude" in self.engine: return self.claude
        return None

    def ask(self, prompt, context=""):
        engine = self._get_active_engine()
        if engine and engine.enabled:
            return engine.ask(prompt, context)
        return "Motor IA no activo o no configurado."

    def analyze_vulnerabilities(self, report_data):
        engine = self._get_active_engine()
        if engine and engine.enabled:
            return engine.analyze_vulnerabilities(report_data)
        return "Análisis por IA no disponible. Revisa tu API Key."

    def generate_password_ai(self, prompt="Genera una contraseña segura"):
        """Usa el motor de IA activo para sugerir una contraseña basada en razonamiento linguístico contextual."""
        engine = self._get_active_engine()
        if not engine or not engine.enabled:
            return "Error: IA no configurada para generación."
            
        # Detección de intención: ¿Es una instrucción técnica o una historia personal?
        # Si es largo (>10 chars) probablemente sea contexto.
        is_contextual = len(prompt) > 10 and "genera" not in prompt.lower()
        
        if is_contextual:
            system_ctx = (
                "Eres un experto en ciberseguridad. Tu tarea es generar una contraseñas MUY ROBUSTA pero MEMORABLE "
                "basada en la historia o datos que te dará el usuario. "
                "Usa sustituciones leet (a->@, e->3, etc), intercala símbolos, y mezcla mayúsculas. "
                "Longitud mínima: 16 caracteres. "
                "IMPORTANTE: Responde ÚNICAMENTE con la contraseña final generada. Nada más."
            )
            user_msg = f"Contexto del usuario: '{prompt}'. Genera la clave derivada:"
        else:
            system_ctx = "Eres un generador de contraseñas de alta entropía. Genera una clave aleatoria compleja de 20 caracteres."
            user_msg = f"Instrucción: {prompt}. Solo la clave:"

        response = engine.ask(user_msg, context=system_ctx)
        
        # Limpieza estricta de la respuesta (Forensic Sanitization)
        # 1. Quitar comillas si la IA las puso
        clean_pwd = response.strip().strip('"').strip("'")
        # 2. Tomar solo la primera línea si la IA explica algo
        clean_pwd = clean_pwd.split("\n")[0]
        # 3. Quitar prefijos comunes si la IA desobedeció
        clean_pwd = clean_pwd.replace("Clave:", "").replace("Password:", "").strip()
        
        return clean_pwd

    def calculate_entropy(self, password):
        """Calcula la entropía de Shanon para medir la predictibilidad real."""
        if not password:
            return 0
        
        # Tamaño del alfabeto
        alphabet_size = 0
        if re.search(r'[a-z]', password): alphabet_size += 26
        if re.search(r'[A-Z]', password): alphabet_size += 26
        if re.search(r'[0-9]', password): alphabet_size += 10
        if re.search(r'[^a-zA-Z0-9]', password): alphabet_size += 32
        
        if alphabet_size == 0: return 0
        
        # Entropía = L * log2(Alfabeto)
        entropy = len(password) * math.log2(alphabet_size)
        return round(entropy, 1)

    def _get_service_impact(self, service_name):
        """Determina la importancia crítica del servicio."""
        s = service_name.lower()
        if any(x in s for x in self.impact_keywords['CRITICAL']): return "CRITICAL" # Email/Infraestructura
        if any(x in s for x in self.impact_keywords['FINANCIAL']): return "FINANCIAL" # Dinero
        if any(x in s for x in self.impact_keywords['SOCIAL']): return "SOCIAL"    # Identidad
        return "STANDARD"

    def _analyze_composition(self, password):
        """Devuelve flags sobre qué tipos de caracteres usa."""
        return {
            "has_upper": bool(re.search(r'[A-Z]', password)),
            "has_lower": bool(re.search(r'[a-z]', password)),
            "has_digit": bool(re.search(r'[0-9]', password)),
            "has_special": bool(re.search(r'[^a-zA-Z0-9]', password))
        }

    def analyze_audit(self, logs):
        """
        Analiza los logs de auditoría para detectar comportamientos sospechosos
        o métricas de uso de la bóveda.
        """
        stats = {
            "total_events": len(logs),
            "critical_events": 0,
            "most_active_user": "Ninguno",
            "most_viewed_service": "Ninguno",
            "actions_summary": Counter()
        }
        
        if not logs:
            return stats

        users = []
        services = []
        
        for log in logs:
            if isinstance(log, dict):
                action = log.get("action", "-")
                user = log.get("user_name", "-")
                service = log.get("service", "-")
            else:
                # Fallback para tuples (timestamp, user_name, action, service, details, device_info, status)
                action = log[2]
                user = log[1]
                service = log[3]
            
            stats["actions_summary"][action] += 1
            if action in ["ELIMINACION FISICA", "ELIMINACION PRIVADA FISICA", "PURGAR NUBE"]:
                stats["critical_events"] += 1
                
            users.append(user)
            if service: services.append(service)

        if users:
            stats["most_active_user"] = Counter(users).most_common(1)[0][0]
        if services:
            stats["most_viewed_service"] = Counter(services).most_common(1)[0][0]
            
        return stats

    def analyze_vault(self, records, audit_logs=None, current_user=None):
        """
        Realiza un análisis profundo y eficiente (O(N)) de la salud y estrategia de la bóveda.
        """
        report = {
            "score": 100,
            "status": "Excelente",
            "findings": [],
            "stats": {
                "total": len(records),
                "analyzed": 0,
                "errors": 0,
                "reused": 0,
                "weak": 0,
                "patterns": 0,
                # Métricas específicas del usuario (Elite Filter)
                "user_total": 0,
                "user_weak": 0,
                "user_refused": 0
            },
            # SECCIÓN ESTRATÉGICA NUEVA
            "strategic_context": {
                "high_impact_services": [], # Servicios críticos detectados
                "composition_deficits": {"no_symbols": 0, "no_numbers": 0, "all_lower": 0},
                "oldest_record_days": 0,
                "average_age_days": 0,
                "stale_passwords": 0 # Claves antiguas > 1 año
            },
            "audit_summary": None,
            "system_integrity": {
                "hwid_enforced": True,
                "sync_status": "Perfect (UUID)",
                "local_db_health": "Healthy"
            },
            "current_user": current_user
        }

        # --- AUDITORÍA DE COMPORTAMIENTO ---
        if audit_logs:
            report["audit_summary"] = self.analyze_audit(audit_logs)
            if report["audit_summary"]["critical_events"] > 0:
                report["findings"].append({
                    "type": "danger",
                    "title": "Actividad Crítica Detectada",
                    "desc": f"Se han registrado {report['audit_summary']['critical_events']} eventos de eliminación física. Verifique la auditoría."
                })

        if not records:
            return report

        seen_passwords = {}
        pass_patterns = []
        current_user_upper = current_user.upper() if current_user else None
        
        total_age_days = 0
        valid_dates = 0
        now = datetime.now()

        for r in records:
            pwd = r.get("secret", "")
            service = r.get("service", "Desconocido")
            owner = str(r.get("owner_name") or "").upper()
            created_at_str = r.get("created_at", "") # Fecha de creación (proxy de antigüedad)
            
            is_my_record = (current_user_upper == owner)

            if is_my_record:
                report["stats"]["user_total"] += 1

            # 1. Filtro de Auditoría: ¿Podemos leer la clave?
            if "[⚠️ Error" in pwd or "ave]" in pwd or not pwd:
                report["stats"]["errors"] += 1
                if is_my_record:
                    report["stats"]["user_refused"] += 1
                continue

            report["stats"]["analyzed"] += 1
            
            # --- ANÁLISIS ESTRATÉGICO DE METADATOS (Nuevo) ---
            
            # A. Impacto del Servicio
            impact = self._get_service_impact(service)
            if impact in ["CRITICAL", "FINANCIAL"]:
                # Solo guardamos el nombre si es relevante para no saturar memoria
                report["strategic_context"]["high_impact_services"].append(f"{service} ({impact})")
            
            # B. Higiene / Antigüedad
            days_old = 0
            if created_at_str:
                try:
                    # Supabase devuelve ISO 8601 (ej. 2024-01-01T12:00:00+00:00)
                    # Python 3.7+ fromisoformat maneja timestamps básicos, a veces requiere quitar la Z
                    iso_clean = created_at_str.replace('Z', '+00:00')
                    dt = datetime.fromisoformat(iso_clean)
                    # Convert to timezone unaware for subtraction if needed, or both aware
                    if dt.tzinfo:
                        dt = dt.replace(tzinfo=None) # Simplificación local
                    delta = now - dt
                    days_old = delta.days
                    
                    total_age_days += days_old
                    valid_dates += 1
                    
                    if days_old > 365:
                        report["strategic_context"]["stale_passwords"] += 1
                        
                    if days_old > report["strategic_context"]["oldest_record_days"]:
                        report["strategic_context"]["oldest_record_days"] = days_old
                        
                except Exception:
                    pass # Ignorar fechas malformadas
            
            # C. Composición
            comp = self._analyze_composition(pwd)
            if not comp['has_special']: 
                report["strategic_context"]["composition_deficits"]["no_symbols"] += 1
            if not comp['has_digit']: 
                report["strategic_context"]["composition_deficits"]["no_numbers"] += 1
            if comp['has_lower'] and not comp['has_upper'] and not comp['has_digit'] and not comp['has_special']:
                 report["strategic_context"]["composition_deficits"]["all_lower"] += 1

            # 2. Detección de Reutilización (Core)
            clean_pwd = pwd.strip()
            if clean_pwd in seen_passwords:
                seen_passwords[clean_pwd].append(service)
                report["stats"]["reused"] += 1
            else:
                seen_passwords[clean_pwd] = [service]

            # 3. Detección de Debilidad Heurística (Core)
            is_weak = False
            for pattern in self.weak_patterns:
                if re.search(pattern, pwd, re.IGNORECASE):
                    is_weak = True
                    break
            
            entropy = self.calculate_entropy(pwd)
            is_weak_entropy = entropy < 50 # Subido el estándar un poco
            
            if is_weak or is_weak_entropy:
                report["stats"]["weak"] += 1
                if is_my_record: report["stats"]["user_weak"] += 1
                
                # REGLA DE MAPA DE CALOR:
                # Si es un servicio CRÍTICO y la clave es DEBIL -> Finding DANGER
                severity = "danger" if impact in ["CRITICAL", "FINANCIAL"] else "warning"
                risk_msg = "RIESGO ALTO (Servicio Crítico)" if impact in ["CRITICAL", "FINANCIAL"] else "Seguridad Baja"
                
                report["findings"].append({
                    "type": severity,
                    "title": f"Vulnerabilidad en {service}",
                    "desc": f"[{risk_msg}] Entropía: {entropy}. Antigüedad: ~{days_old} días."
                })
            
            # 4. Análisis de Patrones (Core)
            suffix = pwd[-4:] if len(pwd) > 4 else None
            if suffix: pass_patterns.append(suffix)

        # Cálculos Finales de Agregados
        if valid_dates > 0:
            report["strategic_context"]["average_age_days"] = int(total_age_days / valid_dates)

        # Hallazgos de reutilización
        for pwd, services in seen_passwords.items():
            if len(services) > 1:
                # Verificar impacto de reutilización
                has_critical = any(self._get_service_impact(s) == "CRITICAL" for s in services)
                severity = "danger" if has_critical else "warning"
                title = "⚠️ REUTILIZACIÓN CRÍTICA" if has_critical else "Contraseña Reutilizada"
                
                report["findings"].append({
                    "type": severity,
                    "title": title,
                    "desc": f"Misma llave en {len(services)} sitios: {', '.join(services[:5])}..."
                })

        # Alerta de Patrones Comunes
        if pass_patterns:
            most_common_suffix = Counter(pass_patterns).most_common(1)
            if most_common_suffix and most_common_suffix[0][1] > 2:
                report["findings"].append({
                    "type": "info",
                    "title": f"Patrón Repetitivo '{most_common_suffix[0][0]}'",
                    "desc": f"Este final se repite en {most_common_suffix[0][1]} claves. Un atacante podría predecirlo."
                })
        
        # 🚨 ADVERTENCIA DE PUNTOS CIEGOS
        if report["stats"]["user_refused"] > 0:
            report["findings"].append({
                "type": "danger",
                "title": "Puntos Ciegos Detectados",
                "desc": f"Tienes {report['stats']['user_refused']} registros indescifrables. Requieren re-sincronización."
            })

        # Calcular Score Final con penalización por impacto
        penalty = (report["stats"]["reused"] * 15) + (report["stats"]["weak"] * 20)
        # Penalización extra si hay servicios críticos expuestos
        critical_vulns = [f for f in report["findings"] if f['type'] == 'danger']
        penalty += (len(critical_vulns) * 10)

        if report["stats"]["analyzed"] == 0 and report["stats"]["errors"] > 0:
            report["score"] = 0
            report["status"] = "Desconocido"
        else:
            report["score"] = max(0, 100 - penalty)
            if report["score"] < 50: report["status"] = "Crítico"
            elif report["score"] < 75: report["status"] = "Riesgoso"
            elif report["score"] < 90: report["status"] = "Mejorable"
        
        return report

    def sanitize_report_for_ai(self, report, max_findings=50):
        """
        Prepara el reporte para envío a IA, incluyendo ahora el contexto estratégico.
        """
        if not report: return {}

        safe = {
            "score": report.get("score"),
            "status": report.get("status"),
            "stats": report.get("stats", {}),
            "strategic_context": report.get("strategic_context", {}), # Inyectar metadatos
            "findings": []
        }

        # Priorizar hallazgos más graves
        findings = sorted(report.get("findings", []), key=lambda x: x.get('type') == 'danger', reverse=True)
        findings = findings[:max_findings]
        
        for f in findings:
            safe["findings"].append({
                "type": f.get("type"),
                "title": f.get("title"),
                "desc": f.get("desc")
            })

        return safe

    def get_smart_suggestion(self, query, records):
        """Búsqueda semántica básica por similitud de texto."""
        if not query or not records:
            return None
        
        services = [r["service"] for r in records]
        matches = difflib.get_close_matches(query, services, n=1, cutoff=0.3)
        
        if matches:
            return f"¿Quizás buscas '{matches[0]}'?"
        return None

    def calculate_crack_time(self, entropy):
        """
        Convierte la entropía en un tiempo estimado de crackeo.
        Asume una capacidad de 10^11 intentos por segundo (Fuerza bruta de GPU potente).
        """
        if entropy <= 0:
            return "Instantáneo"
        
        # Número total de combinaciones: 2^entropía
        combinations = math.pow(2, entropy)
        
        # Segundos para crackear (promedio se asume combinaciones / 2)
        seconds = (combinations / 2) / 1e11 
        
        if seconds < 1: return "Milisegundos"
        if seconds < 60: return f"{int(seconds)} segundos"
        if seconds < 3600: return f"{int(seconds/60)} minutos"
        if seconds < 86400: return f"{int(seconds/3600)} horas"
        if seconds < 31536000: return f"{int(seconds/86400)} días"
        if seconds < 31536000000: return f"{int(seconds/31536000)} años"
        return "Siglos o milenios"
        
        
        
        
