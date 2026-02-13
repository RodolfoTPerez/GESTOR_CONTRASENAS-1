/**
 * Sistema de Mensajería de Alto Nivel - PassGuardian Mobile
 * Estilo: Industrial / Cyber-Ops / Hardware-Security
 */
export const MESSAGES = {
    LANG: "ES",

    _DATA: {
        ES: {
            COMMON: {
                TITLE_ERROR: "ANOMALÍA DETECTADA",
                TITLE_SUCCESS: "OPERACIÓN CONFIRMADA",
                TITLE_INFO: "REPORTE DE ESTADO",
                TITLE_QUESTION: "REQUiere AUTORIZACIÓN",
                BTN_YES: "EJECUTAR",
                BTN_NO: "ABORTAR"
            },
            LOGIN: {
                WELCOME: "TERMINAL DE ACCESO",
                SUBTITLE: "Ingrese firma maestra para desbloqueo de bóveda",
                REG_WELCOME: "INICIALIZAR IDENTIDAD",
                REG_SUBTITLE: "Forjando nueva llave en el perímetro local",
                LOCKED_TITLE: "BÓVEDA SELLADA",
                UNLOCKING: "Cargando perfil criptográfico...",
                TITLE_BLOCKED: "ACCESO BLOQUEADO",
                BTN_LOGIN: "INICIAR SECUENCIA DE DESBLOQUEO",
                BTN_REG: "FORJAR IDENTIDAD",
                REG_LINK: "¿Sin credenciales? Solicite acceso aquí",
                BTN_BACK_LOGIN: "Volver a Terminal",
                TITLE_FIELDS_REQ: "FALTA DE DATOS",
                TEXT_FIELDS_REQ: "Se requiere Identificador y Firma Maestra para validar la secuencia.",
                TITLE_AUTH_ERROR: "AUTENTICACIÓN RECHAZADA",
                TEXT_WRONG_PWD: "Fallo de paridad: La firma no coincide con el registro.",
                TITLE_SETUP_REQ: "INICIALIZACIÓN REQUERIDA",
                LABEL_EMAIL: "IDENTIFICADOR (EMAIL)",
                LABEL_PWD: "FIRMA MAESTRA",
                LABEL_USER: "ALIAS DE OPERADOR",
                PLACEHOLDER_PWD: "••••••••••••",
                PLACEHOLDER_EMAIL: "id@guardian.core"
            },
            DASHBOARD: {
                TITLE: "BÓVEDA ACTIVA",
                SUBTITLE: "{count} nodos de datos detectados",
                SYNC: "🔄 SINCRONIZAR NODOS",
                ADD: "➕ NUEVO REGISTRO",
                STATUS_ONLINE: "📡 ENLACE ACTIVO",
                STATUS_OFFLINE: "📵 MODO AISLADO",
                LOGOUT: "CERRAR Y SELLAR",
                TITLE_ADDED: "REGISTRO SELLADO",
                TEXT_ADDED: "Dato encriptado e integrado en la base de datos.",
                TITLE_COPY: "COPIADO",
                TEXT_COPY_SUCCESS: "Dato capturado en el búfer temporal.",
                FOOTER_DISCLAIMER: "🛡️ BLINDAJE ACTIVO: AES-256-GCM Hardware-Accelerated",
                SEARCH: "🔍 Filtrar por metadatos..."
            },
            VAULT: {
                TITLE_SECURITY: "ALERTA DE SEGURIDAD",
                TITLE_CRITICAL: "ANOMALÍA CRÍTICA",
                TEXT_LOAD_FAIL: "Fallo al montar la partición: {error}"
            }
        }
    },

    get(section, key) {
        try {
            return this._DATA[this.LANG][section][key];
        } catch (e) {
            return `[${section}.${key}]`;
        }
    }
};

export const MSG = {
    COMMON: new Proxy({}, { get: (_, key) => MESSAGES.get('COMMON', key) }),
    LOGIN: new Proxy({}, { get: (_, key) => MESSAGES.get('LOGIN', key) }),
    DASHBOARD: new Proxy({}, { get: (_, key) => MESSAGES.get('DASHBOARD', key) }),
    VAULT: new Proxy({}, { get: (_, key) => MESSAGES.get('VAULT', key) }),
};
