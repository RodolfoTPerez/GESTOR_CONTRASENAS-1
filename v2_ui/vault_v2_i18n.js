/**
 * PassGuardian v2 - Internationalization & Tactical Data
 * Modularized for clean architecture.
 */

const I18N = {
    // UI Global
    'aes_encrypted': { EN: 'AES-256 ENCRYPTED', ES: 'CIFRADO AES-256' },
    'it_security': { EN: 'IT SECURITY OPS', ES: 'OPS SEGURIDAD IT' },

    // Headers & Labels
    'global_security_title': { EN: 'GLOBAL SECURITY STATE', ES: 'ESTADO GLOBAL DE SEGURIDAD' },
    'core_active': { EN: '[CORE_ACTIVE]', ES: '[NÚCLEO_ACTIVO]' },
    'core_health': { EN: 'CORE HEALTH', ES: 'ESTADO DEL NÚCLEO' },
    'access_integrity': { EN: 'ACCESS INTEGRITY', ES: 'INTEGRIDAD DE ACCESO' },
    'encryption_level': { EN: 'ENCRYPTION LEVEL', ES: 'NIVEL DE CIFRADO' },
    'memory_load': { EN: 'MEMORY LOAD', ES: 'CARGA DE MEMORIA' },
    'risk_exposure': { EN: 'RISK EXPOSURE', ES: 'EXPOSICIÓN AL RIESGO' },
    'audit_protocol': { EN: 'AUDIT PROTOCOL', ES: 'PROTOCOLO DE AUDITORÍA' },
    'ai_guardian_title': { EN: 'AI_GUARDIAN / IA_GUARDIÁN', ES: 'IA_GUARDIÁN / AI_GUARDIAN' },
    'risks': { EN: 'RISKS', ES: 'RIESGOS' },
    'pass_health_title': { EN: 'PASSWORD HEALTH', ES: 'SALUD DE CONTRASEÑAS' },
    'sec_watch_title': { EN: 'SECURITY WATCH', ES: 'VIGILANCIA DE SEGURIDAD' },
    'real_time': { EN: '[REAL_TIME]', ES: '[TIEMPO_REAL]' },
    'deep_scan': { EN: '[DEEP_SCAN]', ES: '[ESCANEO_PROFUNDO]' },
    'admin_secrets': { EN: 'ADMIN SECRETS', ES: 'SECRETOS ADMIN' },
    'user_secrets': { EN: 'USERS SECRETS', ES: 'SECRETOS USUARIO' },
    'total_users_lbl': { EN: 'TOTAL USERS', ES: 'TOTAL USUARIOS' },
    'sessions_lbl': { EN: 'SESSIONS', ES: 'SESIONES' },
    'logs_lbl': { EN: 'LOGS', ES: 'REGISTROS' },
    'access_security_title': { EN: 'SECURITY ACCESS', ES: 'SEGURIDAD DE ACCESO' },
    'protection_reinforced': { EN: 'PROTECTION: REINFORCED', ES: 'PROTECCIÓN: REFORZADA' },
    'tactical_radar_live': { EN: 'TACTICAL RADAR: LIVE', ES: 'RADAR TÁCTICO: ACTIVO' },
    'det_vuln': { EN: 'DETECTION: VULNERABILITIES', ES: 'DETECCIÓN: VULNERABILIDADES' },
    'heur_analysis': { EN: 'Heuristic analysis in progress...', ES: 'Análisis heurístico en curso...' },
    'sys_state': { EN: 'System State:', ES: 'Estado del Sistema:' },
    'sec_nodes': { EN: 'Security Nodes:', ES: 'Nodos de Seguridad:' },
    'high_risk': { EN: 'HIGH-RISK', ES: 'ALTO RIESGO' },
    '30d_unused': { EN: '30D UNUSED', ES: '30D SIN USO' },
    'never_rot': { EN: 'NEVER ROT', ES: 'SIN ROTACIÓN' },
    'users_nav': { EN: 'USERS', ES: 'USUARIOS' },
    'audit_nav': { EN: 'AUDIT', ES: 'AUDITORÍA' },
    'monitor_nav': { EN: 'MONITOR', ES: 'MONITOR' },
    'integrity_nav': { EN: 'INTEGRITY', ES: 'INTEGRIDAD' },
    'sync_nav': { EN: 'SYNC', ES: 'SINCRONIZAR' },
    'services_nav': { EN: 'SERVICES', ES: 'SERVICIOS' },
    'active_lbl': { EN: 'ACTIVE:', ES: 'ACTIVOS:' },
    'filtered_lbl': { EN: 'FILTERED:', ES: 'FILTRADOS:' },
    'last_access_hdr': { EN: 'LAST_ACCESS', ES: 'ÚLTIMO_ACCESO' },
    'shield_hdr': { EN: 'SHIELD', ES: 'ESCUDO' },
    'id_hdr': { EN: 'IDENTIFIER', ES: 'IDENTIFICADOR' },
    'owner_hdr': { EN: 'OWNER', ES: 'PROPIETARIO' },
    'pass_hdr': { EN: 'PASSWORD', ES: 'CONTRASEÑA' },
    'notes_hdr': { EN: 'NOTES', ES: 'NOTAS' },
    'action_hdr': { EN: 'ACTION', ES: 'ACCIÓN' },
    'service_hdr': { EN: 'SERVICE', ES: 'SERVICIO' },
    'details_hdr': { EN: 'DETAILS', ES: 'DETALLES' },

    // Status & Dynamic
    'attempts': { EN: 'ATTEMPTS', ES: 'INTENTOS' },
    'active': { EN: 'ACTIVE', ES: 'ACTIVO' },
    'safe': { EN: 'SAFE', ES: 'SEGURO' },
    'good': { EN: 'GOOD', ES: 'BUENO' },
    'warning': { EN: 'WARNING', ES: 'ADVERTENCIA' },
    'critical': { EN: 'CRITICAL', ES: 'CRÍTICO' },
    'nominal': { EN: 'NOMINAL', ES: 'NOMINAL' },
    'just_now': { EN: 'JUST NOW', ES: 'AHORA MISMO' },
    'vuln_detected': { EN: 'Critical vulnerability detected in', ES: 'Vulnerabilidad crítica detectada en' },
    'vaults': { EN: 'vaults', ES: 'bóvedas' },
    'vault': { EN: 'vault', ES: 'bóveda' },
    'apply': { EN: 'APPLY', ES: 'APLICAR' },
    'review': { EN: 'REVIEW', ES: 'REVISAR' },
    'ignore': { EN: 'IGNORE', ES: 'IGNORAR' },
    'degraded_posture': { EN: 'WARNING: Degraded security posture', ES: 'ADVERTENCIA: Postura de seguridad degradada' },
    'key_scan_done': { EN: 'Key scan completed:', ES: 'Escaneo de claves completado:' },
    'nodes_prot': { EN: 'nodes protected', ES: 'nodos protegidos' },
    'vectors_det': { EN: 'attack vectors detected', ES: 'vectores de ataque detectados' },
    'multi_sessions': { EN: 'Multiple active sessions detected', ES: 'Múltiples sesiones activas detectadas' },
    'nominal_params': { EN: 'System operating within nominal parameters', ES: 'Sistema operando bajo parámetros nominales' },
    'mfa_coverage': { EN: 'MFA COVERAGE', ES: 'COBERTURA MFA' },
    'admin_sec': { EN: 'ADMIN SECURITY', ES: 'SEGURIDAD DE ADMIN' },
    'active_sessions': { EN: 'ACTIVE SESSIONS', ES: 'SESIONES ACTIVAS' },
    'sec_policy': { EN: 'SECURITY POLICY', ES: 'POLÍTICA DE SEGURIDAD' },
    'login_attempts': { EN: 'LOGIN ATTEMPTS', ES: 'INTENTOS LOGIN' },
    'last_incident': { EN: 'LAST INCIDENT', ES: 'ÚLTIMO INCIDENTE' },
    'last_scan': { EN: 'Last scan:', ES: 'Último escaneo:' },
    'weak_lbl': { EN: 'WEAK', ES: 'DÉBILES' },
    'strong_lbl': { EN: 'STRONG', ES: 'FUERTES' },
    'repeated_lbl': { EN: 'REPEATED', ES: 'REPETIDAS' },
    'expired_lbl': { EN: 'EXPIRED', ES: 'EXPIRADAS' },
    'health_lbl': { EN: 'HEALTH', ES: 'SALUD' },
    'fix_issues_btn': { EN: 'FIX ISSUES', ES: 'REPARAR' },
    'dbl_click_details': { EN: 'Double-click for details', ES: 'Doble click para detalles' },
    'reveal': { EN: 'REVEAL', ES: 'REVELAR' },
    'copy': { EN: 'COPY', ES: 'COPIAR' },
    'terminate_node_prompt': { EN: 'TERMINATE NODE', ES: 'TERMINAR NODO' },
    'node_purgued': { EN: 'NODE_PURGED_SUCCESSFULLY', ES: 'COMPONENTE_PURGADO_CON_ÉXITO' },
    'purge_failure': { EN: 'PURGE_PROTOCOL_FAILURE', ES: 'ERROR_EN_PROTOCOLO_DE_PURGA' },
    'secret_piped': { EN: 'SECRET_PIPED_TO_CLIPBOARD', ES: 'SECRETO_PIPED_A_PORTAPAPELES' },
    'copy_unauth': { EN: 'COPY_FAILURE: UNAUTHORIZED', ES: 'FALLO_DE_COPIA: NO_AUTORIZADO' },
    'decryption_active': { EN: 'DECODING_NOMINAL_ACTIVE', ES: 'DECODIFICACIÓN_NOMINAL_ACTIVA' },
    'security_title': { EN: 'SECURITY', ES: 'SEGURIDAD' },
    'sync_title': { EN: 'SYNC', ES: 'SINCRONIZACIÓN' },
    'critical_error': { EN: 'CRITICAL ERROR', ES: 'ERROR CRÍTICO' },
    'vault_system': { EN: 'VAULT SYSTEM', ES: 'SISTEMA BÓVEDA' },
    'vault_error': { EN: 'VAULT ERROR', ES: 'ERROR BÓVEDA' },
    'secret_remasked': { EN: 'SECRET_RE-MASKED', ES: 'SECRETO_RE-ENMASCARADO' },
    'access_denied_title': { EN: 'ACCESS_DENIED', ES: 'ACCESO_DENEGADO' },
    'reveal_protocol_failure': { EN: 'REVEAL_PROTOCOL_FAILURE', ES: 'FALLO_PROTOCOLO_REVELADO' },
    'bridge_disconnected': { EN: 'BRIDGE_DISCONNECTED', ES: 'PUENTE_DESCONECTADO' },
    'initializing_protocol': { EN: 'INITIALIZING_PROTOCOL...', ES: 'INICIALIZANDO_PROTOCOLO...' },
    'initializing_link': { EN: 'INITIALIZING_SECURE_LINK...', ES: 'INICIALIZANDO_ENLACE_SEGURO...' },
    'just_now': { EN: 'JUST_NOW', ES: 'JUSTO_AHORA' },

    // Sidebar Navigation
    'nav_dashboard': { EN: 'DASHBOARD', ES: 'DASHBOARD' },
    'nav_vault': { EN: 'VAULT', ES: 'BÓVEDA' },
    'nav_ai_guardian': { EN: 'AI GUARDIAN', ES: 'GUARDIÁN IA' },
    'nav_activity': { EN: 'ACTIVITY LOG', ES: 'REGISTRO DE ACTIVIDAD' },
    'nav_users': { EN: 'ADMIN PANEL', ES: 'PANEL DE CONTROL' },
    'nav_settings': { EN: 'SETTINGS', ES: 'CONFIGURACIÓN' },
    'brightness_lbl': { EN: 'BRIGHTNESS_LEVEL', ES: 'NIVEL_DE_BRILLO' },

    // Action Hub
    'btn_sync': { EN: 'SYNC', ES: 'SINCRONIZAR' },
    'btn_import': { EN: 'IMPORT', ES: 'IMPORTAR' },
    'btn_export': { EN: 'EXPORT', ES: 'EXPORTAR' },
    'btn_backup': { EN: 'BACKUP', ES: 'RESPALDO' },
    'btn_restore': { EN: 'RESTORE', ES: 'RESTAURAR' },
    'btn_ai_audit': { EN: 'AI AUDIT', ES: 'AUDITORÍA IA' },
    'search_logs': { EN: 'SEARCH_LOGS...', ES: 'BUSCAR_REGISTROS...' },
    'filter_all': { EN: 'ALL_EVENTS', ES: 'TODOS_LOS_EVENTOS' },
    'filter_login': { EN: 'LOGIN_SESSIONS', ES: 'SESIONES_DE_LOGIN' },
    'filter_vault': { EN: 'VAULT_ACTIONS', ES: 'ACCIONES_DE_BOVEDA' },
    'filter_admin': { EN: 'ADMIN_CHANGES', ES: 'CAMBIOS_ADMIN' },
    'ai_analysis_feed': { EN: 'AI_ANALYSIS_FEED', ES: 'FLUJO_DE_ANÁLISIS_IA' },
    'intel_active': { EN: 'NEURAL_INTELLIGENCE_ACTIVE', ES: 'INTELIGENCIA_NEURONAL_ACTIVA' },
    'ai_proto_connected': { EN: 'AI_PROTOCOL: GEMINI_CORE_LINKED', ES: 'PROTOCOLO_IA: NÚCLEO_GÉMINIS_CONECTADO' },
    'ai_analyzing_vault': { EN: 'ANALYZING_VAULT: {}_NODES_DETECTED', ES: 'ANALIZANDO_BOVEDA: {}_NODOS_DETECTADOS' },
    'ai_op_integrity': { EN: 'OPERATIONAL_INTEGRITY: {}%', ES: 'INTEGRIDAD_OPERACIONAL: {}%' },
    'ai_risk_state': { EN: 'RISK_STATE: {}', ES: 'ESTADO_DE_RIESGO: {}' },
    'ai_mfa_status': { EN: 'MFA_ADMIN_STATUS: {}', ES: 'ESTADO_ADMIN_MFA: {}' },
    'ai_attack_patterns': { EN: 'ATTACK_PATTERNS: {}', ES: 'PATRONES_DE_ATAQUE: {}' },
    'ai_system_mode': { EN: 'GEMINI_MODE: {}', ES: 'MODO_GÉMINIS: {}' },
    'ai_threat_alert': { EN: 'ALERT: {}_RISK_VECTORS_DETECTED', ES: 'ALERTA: {}_VECTORES_DE_RIESGO_DETECTADOS' },
    'ai_vulnerable': { EN: 'VULNERABLE (MFA_INACTIVE)', ES: 'VULNERABLE (MFA_DESACTIVADO)' },
    'ai_protected': { EN: 'ENFORCED_PROTECTION', ES: 'PROTECCIÓN_REFORZADA' },
    'ai_detected': { EN: 'DETECTED', ES: 'DETECTADO' },
    'ai_none': { EN: 'NONE', ES: 'NINGUNO' },
    'ai_active_prot': { EN: 'ACTIVE_SHIELD_ENGAGED', ES: 'ESCUDO_ACTIVO_ACOPLADO' },
    'ai_watch_mode': { EN: 'VIGILANT_MODE', ES: 'MODO_VIGILANTE' },
    'ai_neural_ident': { EN: 'NEURAL_IDENTIFICATION', ES: 'IDENTIFICACIÓN_NEURONAL' },
    'ai_deep_scan_ok': { EN: 'Deep Scan Completed. Gemini Engine reports nominal integrity.', ES: 'Análisis profundo completado. Gemini Engine reporta integridad nominal.' },
    'user_registry': { EN: 'USER_REGISTRY', ES: 'REGISTRO_DE_USUARIOS' },
    'btn_lock': { EN: 'LOCK', ES: 'BLOQUEAR' },
    'btn_unlock': { EN: 'UNLOCK', ES: 'DESBLOQUEAR' },
    'btn_details': { EN: 'DETAILS', ES: 'DETALLES' },
    'operator_lbl': { EN: 'OPERATOR_ID', ES: 'ID_DE_OPERADOR' },
    'key_rotation': { EN: 'LAST_KEY_ROTATION', ES: 'ÚLTIMA_ROTACIÓN_DE_LLAVE' },
    'last_synced': { EN: 'CLOUD_SYNC_STATUS', ES: 'ESTADO_DE_SINCRONIZACIÓN' },
    'auto_lock_protocol': { EN: 'AUTO_LOCK_PROTOCOL', ES: 'PROTOCOLO_BLOQUEO_AUTOMÁTICO' },
    'network_layer': { EN: 'NETWORK_INTERFACE', ES: 'INTERFAZ_DE_RED' },
    'encryption_standard': { EN: 'ENCRYPTION_STANDARD', ES: 'ESTÁNDAR_DE_CIFRADO' },
    'invitations_protocol': { EN: 'INVITATIONS_PROTOCOL', ES: 'PROTOCOLO_DE_INVITACIÓN' },
    'gen_code_btn': { EN: 'GEN_CODE', ES: 'GEN_CÓDIGO' },
    'code_hdr': { EN: 'CODE', ES: 'CÓDIGO' },
    'created_by_hdr': { EN: 'CREATED_BY', ES: 'CREADO_POR' },
    'add_node_operator': { EN: 'ADD_NODE_OPERATOR', ES: 'AÑADIR_OPERADOR_NODO' },
    'operator_name': { EN: 'OPERATOR_NAME', ES: 'NOMBRE_DE_OPERADOR' },
    'access_role': { EN: 'ACCESS_ROLE', ES: 'ROL_DE_ACCESO' },
    'master_password': { EN: 'MASTER_PASSWORD', ES: 'CONTRASEÑA_MAESTRA' },
    'provision_node_btn': { EN: 'PROVISION_NODE', ES: 'PROVISIONAR_NODO' },
    'ai_engine_protocol': { EN: 'AI_ENGINE_PROTOCOL', ES: 'PROTOCOLO_MOTOR_IA' },
    'active_engine': { EN: 'ACTIVE_ENGINE', ES: 'MOTOR_ACTIVO' },
    'vault_name_alias': { EN: 'VAULT_NAME_ALIAS', ES: 'ALIAS_DE_LA_BOVEDA' },
    'ui_theme_protocol': { EN: 'UI_THEME_PROTOCOL', ES: 'PROTOCOLO_TEMA_UI' },
    'system_recovery': { EN: 'SYSTEM_RECOVERY', ES: 'RECUPERACIÓN_DEL_SISTEMA' },
    'launch_repair': { EN: 'LAUNCH_REPAIR', ES: 'INICIAR_REPARACIÓN' },
    'commit_changes': { EN: 'COMMIT_CHANGES', ES: 'EJECUTAR_CAMBIOS' },
    'user_hdr': { EN: 'USER', ES: 'USUARIO' },
    'role_hdr': { EN: 'ROLE', ES: 'ROL' },
    'state_hdr': { EN: 'STATE', ES: 'ESTADO' },
    'mfa_hdr': { EN: '2FA', ES: '2FA' },
    'lock_hdr': { EN: 'SUSPEND', ES: 'SUSPENDER' },
    'delete_hdr': { EN: 'DELETE', ES: 'BORRAR' },
    'placeholder_operator_id': { EN: 'ID_ALPHA_...', ES: 'ID_ALPHA_...' },
    'user_standard': { EN: 'USER_STANDARD', ES: 'USUARIO_ESTANDAR' },
    'admin_root': { EN: 'ADMIN_ROOT', ES: 'ADMIN_ROOT' },
    'no_active_codes': { EN: '> NO_ACTIVE_CODES', ES: '> SIN_CODIGOS_ACTIVOS' },
    'no_operators_detected': { EN: '> NO_OPERATORS_DETECTED', ES: '> SIN_OPERADORES_DETECTADOS' },
    'current_user_tag': { EN: '(YOU)', ES: '(TÚ)' },
    'tooltip_reset_2fa': { EN: 'RESET 2FA protocol', ES: 'REINICIAR protocolo 2FA' },
    'tooltip_change_pass': { EN: 'CHANGE password protocol', ES: 'CAMBIAR protocolo password' },
    'tooltip_delete': { EN: 'FIRE: delete node', ES: 'FUEGO: eliminar nodo' },
    'tooltip_copy': { EN: 'CLICK to copy', ES: 'CLICK para copiar' },
    'tag_2fa_prot': { EN: '2FA_PROTECTED', ES: '2FA_PROTEGIDO' },
    'tag_2fa_disabled': { EN: '2FA_DISABLED', ES: '2FA_DESACTIVADO' },
    'tooltip_lock': { EN: 'LOCK: Suspend operator', ES: 'BLOQUEAR: Suspender operador' },
    'tooltip_unlock': { EN: 'UNLOCK: Reactive operator', ES: 'DESBLOQUEAR: Reactivar operador' },

    // Services Modal (Cyber-Ops)
    'service_modal_title_new': { EN: 'NEW_NODE_INTEGRATION', ES: 'INTEGRACIÓN_DE_NODO_NUEVO' },
    'service_modal_title_edit': { EN: 'NODE_MODIFICATION [ID:{}]', ES: 'MODIFICACIÓN_DE_NODO [ID:{}]' },
    'service_id_lbl': { EN: 'SERVICE_IDENTIFIER', ES: 'SERVICIO_IDENTIFICADOR' },
    'owner_usr_lbl': { EN: 'OWNER (USR)', ES: 'PROPIETARIO (USR)' },
    'privacy_protocol_lbl': { EN: 'PRIVACY_PROTOCOL', ES: 'PRIVACIDAD_PROTOCOLO' },
    'public_team_opt': { EN: 'TEAM (PUBLIC)', ES: 'EQUIPO (PÚBLICO)' },
    'personal_private_opt': { EN: 'PERSONAL (PRIVATE)', ES: 'PERSONAL (PRIVADO)' },
    'access_key_lbl': { EN: 'ACCESS_KEY (SECRET)', ES: 'LLAVE_DE_ACCESO (SECRETO)' },
    'gen_pro_btn': { EN: 'GENERATE_PRO', ES: 'GENERAR_PRO' },
    'field_notes_lbl': { EN: 'FIELD_NOTES (CONTEXT)', ES: 'NOTAS_DE_CAMPO (CONTEXTO)' },
    'cancel_op_btn': { EN: 'CANCEL_OPERATION', ES: 'CANCELAR_OPERACIÓN' },
    'encrypt_save_btn': { EN: 'ENCRYPT_AND_SAVE', ES: 'ENCRIPTAR_Y_GUARDAR' },
    'security_pending_lbl': { EN: 'SECURITY: PENDING_INPUT', ES: 'SEGURIDAD: PENDIENTE_ENTRADA' },
    'security_status_lbl': { EN: 'SECURITY: {}', ES: 'SEGURIDAD: {}' },
    'placeholder_service': { EN: 'Ex: Google, AWS, Core_Database...', ES: 'Ej: Google, AWS, Core_Database...' },
    'placeholder_notes': { EN: 'Auth details, IP, Backup keys...', ES: 'Detalles de autorización, IP, Backup keys...' },
    'entropy_lbl': { EN: 'ENTROPY', ES: 'ENTROPÍA' },
    'crack_time_lbl': { EN: 'CRACK_TIME', ES: 'TIEMPO_DESCIFRADO' },
    'enter_secret_msg': { EN: 'MUST ENTER SECRET FOR ANALYSIS', ES: 'DEBE INGRESAR SECRETO PARA ANÁLISIS' },
    'persistence_nominal': { EN: 'PERSISTENCE_PROTOCOL_NOMINAL', ES: 'PROTOCOLO_DE_PERSISTENCIA_NOMINAL' },
    'duplicate_service_err': { EN: 'SERVICE_ALREADY_EXISTS_IN_VAULT', ES: 'EL_SERVICIO_YA_EXISTE_EN_LA_BOVEDA' },
    // Sync and Audit Modal (Cyber-Ops)
    'sync_error_fail': { EN: 'ERROR:_SYNC_FAIL', ES: 'ERROR:_FALLO_SINCRO' },
    'sync_ok_status': { EN: 'SYNC_OK:_+{}_- {}', ES: 'SINCRO_OK:_+{}_- {}' },
    'sync_up_to_date': { EN: 'SYNC_UP_TO_DATE', ES: 'SINCRO_AL_DIA' },
    'audit_modal_title': { EN: 'CRITICAL_AUDIT_LOG', ES: 'REGISTRO_CRÍTICO_DE_AUDITORÍA' },
    'audit_col_time': { EN: 'TIME_STAMP', ES: 'FECHA_HORA' },
    'audit_col_usr': { EN: 'USR', ES: 'USR' },
    'audit_col_action': { EN: 'ACTION', ES: 'ACCIÓN' },
    'audit_col_service': { EN: 'SERVICE', ES: 'SERVICIO' },
    'audit_col_details': { EN: 'DETAILS', ES: 'DETALLES' },
    'audit_col_status': { EN: 'STATUS', ES: 'ESTADO' },

    // Sessions Monitor Modal (Cyber-Ops)
    'monitor_modal_title': { EN: 'ACTIVE_SESSIONS_MONITOR', ES: 'MONITOR_DE_SESIONES_ACTIVAS' },
    'monitor_col_node': { EN: 'NODE', ES: 'NODO' },
    'monitor_col_ip': { EN: 'SOURCE_IP', ES: 'ORIGEN_IP' },
    'monitor_col_started': { EN: 'STARTED', ES: 'INICIO' },
    'monitor_col_status': { EN: 'STATUS', ES: 'ESTADO' },
    'monitor_col_action': { EN: 'ACTION', ES: 'ACCIÓN' },
    'no_active_sessions': { EN: 'NO ACTIVE SESSIONS FOUND', ES: 'NO HAY SESIONES ACTIVAS' },
    'session_active': { EN: 'ACTIVE', ES: 'ACTIVA' },
    'session_stale': { EN: 'INACTIVE_STALE', ES: 'INACTIVA_STALE' },
    'btn_kill': { EN: 'TERMINATE', ES: 'TERMINAR' },
    'confirm_kill_session': { EN: 'Remotely terminate this session?', ES: '¿Terminar esta sesión remotamente?' },

    // Health / Intelligence Scanner
    'health_total_vault': { EN: 'TOTAL_VAULT', ES: 'TOTAL_VAULT' },
    'health_user_total': { EN: 'USR_TOTAL', ES: 'USR_TOTAL' },
    'health_vulnerable': { EN: 'VULNERABLES', ES: 'VULNERABLES' },
    'health_findings_title': { EN: 'SECURITY_FINDINGS_DETAIL', ES: 'DETALLE_DE_HALLAZGOS_DE_SEGURIDAD' },
    'health_no_findings': { EN: 'SYSTEM OPTIMAL. ZERO BREACHES DETECTED.', ES: 'SISTEMA ÓPTIMO. CERO BRECHAS DETECTADAS.' }
};

// GHOST EXPLANATION SYSTEM - BILINGUAL & DETAILED

const GHOST_EXPLANATIONS = {
    "admin_secrets": {
        title: { EN: "ANALYSIS: ADMINISTRATIVE_NODES", ES: "ANÁLISIS: NODOS_ADMIN" },
        body: `
            <p><b>[EN]</b> <b>Function:</b> Tracks high-privilege credentials that govern cross-system infrastructure. 
            <b>Use:</b> Critical for disaster recovery and core system maintenance.
            <b>Status:</b> <span class="v3-status-label good">SAFE</span> if the count is stable and limited to authorized admins. <b>Warning:</b> Unexpected increases indicate potential credential sprawl.</p>
            <p><b>[ES]</b> <b>Función:</b> Rastrea credenciales de alto privilegio que gobiernan la infraestructura del sistema. 
            <b>Uso:</b> Crítico para recuperación de desastres y mantenimiento del núcleo.
            <b>Estado:</b> <span class="v3-status-label good">SEGURO</span> si el conteo es estable y limitado a admins autorizados. <b>Aviso:</b> Incrementos inesperados indican posible dispersión de credenciales.</p>
        `
    },
    "user_secrets": {
        title: { EN: "ANALYSIS: CLIENT_ACCESS_NODES", ES: "ANÁLISIS: NODOS_USUARIO" },
        body: `
            <p><b>[EN]</b> <b>Function:</b> Total count of active standard credentials stored in the vault partition. 
            <b>Use:</b> Core inventory for daily operational access control.
            <b>Status:</b> <span class="v3-status-label teal">NOMINAL</span> as long as each node utilizes unique AES-256 keys. Isolation prevents cross-profile leakage.</p>
            <p><b>[ES]</b> <b>Función:</b> Conteo total de credenciales estándar activas almacenadas en la partición de la bóveda. 
            <b>Uso:</b> Inventario central para el control de acceso operativo diario.
            <b>Estado:</b> <span class="v3-status-label teal">NOMINAL</span> mientras cada nodo utilice llaves AES-256 únicas. El aislamiento previene fugas entre perfiles.</p>
        `
    },
    "total_users_lbl": {
        title: { EN: "ANALYSIS: IDENTITY_DIRECTORY", ES: "ANÁLISIS: DIRECTORIO_IDENTIDADES" },
        body: `
            <p><b>[EN]</b> <b>Function:</b> The complete registry of unique IDs authorized to interact with the system. 
            <b>Use:</b> Managing the trust perimeter and identifying user growth.
            <b>Status:</b> <span class="v3-status-label good">GOOD</span> if matched with HR records. <b>Danger:</b> Zombie accounts (inactive but authorized) should be purged via 'Monitor' panel.</p>
            <p><b>[ES]</b> <b>Función:</b> El registro completo de IDs únicos autorizados para interactuar con el sistema. 
            <b>Uso:</b> Gestión del perímetro de confianza e identificación del crecimiento de usuarios.
            <b>Estado:</b> <span class="v3-status-label good">ÓPTIMO</span> si coincide con registros de RRHH. <b>Peligro:</b> Cuentas zombi (inactivas pero autorizadas) deben purgarse vía el panel 'Monitor'.</p>
        `
    },
    "sessions_lbl": {
        title: { EN: "ANALYSIS: AUTHENTICATION_CONCURRENCY", ES: "ANÁLISIS: CONCURRENCIA" },
        body: `
            <p><b>[EN]</b> <b>Function:</b> Monitors active cryptographic tokens in temporary memory. 
            <b>Use:</b> Identifying real-time system utilization and potential session hijacking attempts.
            <b>Status:</b> <span class="v3-status-label warning">VIGILANCE</span> required if sessions > 3 per unique user. Sudden spikes trigger the 'Auto-Lock' security protocol.</p>
            <p><b>[ES]</b> <b>Función:</b> Monitorea tokens criptográficos activos en memoria temporal. 
            <b>Uso:</b> Identificación de uso del sistema en tiempo real y posibles intentos de secuestro de sesión.
            <b>Estado:</b> <span class="v3-status-label warning">VIGILANCIA</span> requerida si hay más de 3 sesiones por usuario único. Picos repentinos activan el protocolo 'Auto-Lock'.</p>
        `
    },
    "logs_lbl": {
        title: { EN: "ANALYSIS: IMMUTABLE_AUDIT_STREAMS", ES: "ANÁLISIS: FLUJOS_AUDITORÍA" },
        body: `
            <p><b>[EN]</b> <b>Function:</b> Accumulation of digitally signed events in the audit buffer. 
            <b>Use:</b> Forensics and regulatory compliance auditing.
            <b>Status:</b> <span class="v3-status-label good">ACTIVE</span>. <b>Critical:</b> A zero-growth log stream indicates a failure in the logging provider or a bypass attempt.</p>
            <p><b>[ES]</b> <b>Función:</b> Acumulación de eventos firmados digitalmente en el búfer de auditoría. 
            <b>Uso:</b> Forense y auditoría de cumplimiento regulatorio.
            <b>Estado:</b> <span class="v3-status-label good">ACTIVO</span>. <b>Crítico:</b> Un flujo de registros sin crecimiento indica una falla en el proveedor de logs o un intento de bypass.</p>
        `
    },
    "global_security_title": {
        title: { EN: "INTERPRETATION: SECURITY_POSTURE", ES: "INTERPRETACIÓN: POSTURA_SEGURIDAD" },
        body: `
            <p><b>[EN] ANALYSIS:</b> This panel evaluates the structural integrity of the active session through a composite score, dictating the automated engagement of defensive protocols.<br>
            • <b>Core Health:</b> Measures stability of the cryptographic kernel. Critical for preventing cascade failures.<br>
            • <b>Access Integrity:</b> Validates that the current login context remains free from unexpected anomalies or hijacked tokens.<br>
            • <b>Memory Load:</b> Continuous RAM tracking to proactively detect potential memory leak vulnerabilities or injected payloads.<br>
            • <b>Risk Exposure:</b> A raw numeric indicator summing active threats; guides the engagement of the AI Guardian's countermeasures.<br>
            • <b>Audit Protocol:</b> Confirms that local and remote telemetry feeds are untouched and actively logging events.</p>
            
            <p><b>[ES] ANÁLISIS:</b> Este panel evalúa la integridad estructural de la sesión activa mediante un puntaje compuesto, lo cual dicta la activación automatizada de protocolos defensivos.<br>
            • <b>Estado del Núcleo:</b> Mide la estabilidad del kernel criptográfico. Crítico para prevenir fallas en cascada.<br>
            • <b>Integridad de Acceso:</b> Valida que el contexto actual de inicio de sesión permanezca libre de anomalías inesperadas o tokens secuestrados.<br>
            • <b>Carga de Memoria:</b> Rastreo continuo de RAM para detectar proactivamente posibles vulnerabilidades de fuga de memoria o cargas inyectadas.<br>
            • <b>Riesgo:</b> Un indicador numérico bruto que suma las amenazas activas; guía la activación de las contramedidas del Guardián IA.<br>
            • <b>Protocolo de Auditoría:</b> Confirma que los flujos de telemetría locales y remotos están intactos y registrando eventos activamente.</p>
        `
    },
    "ai_guardian_title": {
        title: { EN: "INTERPRETATION: HEURISTIC_RADAR", ES: "INTERPRETACIÓN: RADAR_HEURÍSTICO" },
        body: `
            <p><b>[EN] ANALYSIS:</b> The Tactical Radar maps 8 independent threat vectors in real-time, visualizing the proactive defensive depth of the system's neural sector.<br>
            • <b>Strength, Identity & Risk:</b> Evaluates the core triad of user safety; high entropy, verified user origins, and minimized exposure windows.<br>
            • <b>Logs & Cloud:</b> Ensures backplane synchronization is solid and the flow of immutable events remains unblocked to prevent shadow operations.<br>
            • <b>Health, Rotation & Intel:</b> Gauges adherence to mandatory cryptographic rotation policies and the overall heuristic intelligence scoring.<br>
            <b>Diagnostic:</b> Perfect symmetry across the octagonal sweep indicates maximum defensive posture.</p>

            <p><b>[ES] ANÁLISIS:</b> El Radar Táctico mapea 8 vectores de amenaza independientes en tiempo real, visualizando la profundidad defensiva proactiva del sector neuronal del sistema.<br>
            • <b>Fortaleza, Identidad y Riesgo:</b> Evalúa la tríada central de seguridad del usuario; alta entropía, orígenes de usuario verificados y ventanas de exposición minimizadas.<br>
            • <b>Logs y Cloud:</b> Asegura que la sincronización del plano posterior sea sólida y que el flujo de eventos inmutables no esté bloqueado para prevenir operaciones en la sombra.<br>
            • <b>Salud, Rotación e IA:</b> Mide el cumplimiento de las políticas obligatorias de rotación criptográfica y la puntuación de inteligencia heurística general.<br>
            <b>Diagnóstico:</b> Una simetría perfecta en todo el barrido octagonal indica la máxima postura defensiva.</p>
        `
    },
    "access_security_title": {
        title: { EN: "CONTEXT: PERIMETER_DEFENSES", ES: "CONTEXTO: DEFENSAS_PERIMETRALES" },
        body: `
            <p><b>[EN] ANALYSIS:</b> Monitors the outer shell of the authentication perimeter, tracking unauthorized access attempts.<br>
            • <b>MFA Coverage:</b> Percentage of accounts secured by Multi-Factor Authentication. Crucial defense against credential harvesting.<br>
            • <b>Admin Security & Active Sessions:</b> Tracks elevated privileges and concurrent logins to prevent lateral movement or unauthorized session persistence.<br>
            • <b>Security Policy:</b> Validates the strictness of the operating environment against organizational standards.<br>
            • <b>Login Attempts & Last Incident:</b> A live counter of brute-force efforts and a timestamp of the most recent security perimeter breach.</p>

            <p><b>[ES] ANÁLISIS:</b> Monitorea la capa exterior del perímetro de autenticación, rastreando intentos de acceso no autorizados.<br>
            • <b>Cobertura MFA:</b> Porcentaje de cuentas protegidas por Autenticación Multifactor. Defensa crucial contra la recolección de credenciales.<br>
            • <b>Seguridad de Admin y Sesiones:</b> Rastrea privilegios elevados y logins concurrentes para prevenir movimiento lateral o persistencia no autorizada.<br>
            • <b>Política de Seguridad:</b> Valida la rigurosidad del entorno operativo contra los estándares de la organización.<br>
            • <b>Intentos Login y Último Incidente:</b> Un contador en vivo de esfuerzos de fuerza bruta y una marca de tiempo de la brecha perimetral más reciente.</p>
        `
    },
    "pass_health_title": {
        title: { EN: "CONTEXT: CRYPTOGRAPHIC_VIGILANCE", ES: "CONTEXTO: VIGILANCIA_CRIPTO" },
        body: `
            <p><b>[EN] ANALYSIS:</b> The cryptographic vigilance engine that audits vault entropy and rotation compliance.<br>
            • <b>Weak/Strong Ratio:</b> Analyzes the structural entropy of stored keys against known dictionaries and algorithmic complexity standards.<br>
            • <b>Health Gauge:</b> An overall score of the vault's resilience to offline decryption attempts.<br>
            • <b>Repeated Keys:</b> Measures the compounded risk of a single breach compromising multiple segmented accounts.<br>
            • <b>Expired Keys:</b> Tracks adherence to mandatory time-based cryptographic rotation policies, flagging keys that have outlived their safe lifecycle.</p>

            <p><b>[ES] ANÁLISIS:</b> El motor de vigilancia criptográfica que audita la entropía de la bóveda y el cumplimiento de rotación.<br>
            • <b>Ratio Débil/Fuerte:</b> Analiza la entropía estructural de las llaves almacenadas contra diccionarios conocidos y estándares de complejidad algorítmica.<br>
            • <b>Medidor de Salud:</b> Un puntaje general de la resiliencia de la bóveda ante intentos de descifrado fuera de línea.<br>
            • <b>Llaves Repetidas:</b> Mide el riesgo compuesto de que una sola brecha comprometa múltiples cuentas segmentadas.<br>
            • <b>Llaves Expiradas:</b> Rastrea el cumplimiento de las políticas obligatorias de rotación criptográfica basadas en tiempo, marcando las llaves que han superado su ciclo de vida seguro.</p>
        `
    },
    "sec_watch_title": {
        title: { EN: "CONTEXT: REAL-TIME_TELEMETRY", ES: "CONTEXTO: TELEMETRÍA_EN_TIEMPO_REAL" },
        body: `
            <p><b>[EN] ANALYSIS:</b> A live feed detailing active background scans and hardware infrastructure stability.<br>
            • <b>Threat Detection:</b> Identifies and counts active threats or malformed keys hidden inside the database structure.<br>
            • <b>Database Load (SQLite):</b> Monitors the read/write query volume. Anomalous spikes can indicate payload injection or automated data exfiltration.<br>
            • <b>System State & Nodes:</b> Validates that the core protective partition and its sub-nodes are fully engaged and actively scanning.</p>

            <p><b>[ES] ANÁLISIS:</b> Un feed en vivo que detalla escaneos de fondo activos y la estabilidad de la infraestructura de hardware.<br>
            • <b>Detección de Amenazas:</b> Identifica y cuenta amenazas activas o llaves malformadas escondidas dentro de la estructura de la base de datos.<br>
            • <b>Carga de Base de Datos (SQLite):</b> Monitorea el volumen de consultas de lectura/escritura. Picos anómalos pueden indicar inyección de cargas útiles o exfiltración automatizada de datos.<br>
            • <b>Estado del Sistema y Nodos:</b> Valida que la partición protectora del núcleo y sus subnodos estén completamente activados y escaneando activamente.</p>
        `
    }
};
