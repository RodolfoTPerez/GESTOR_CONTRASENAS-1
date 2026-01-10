🛡️ PROMPT MAESTRO “LOCKED v1.0” — PASSWORD MANAGER DESKTOP PYTHON

Rol de la IA: Arquitecto jefe y desarrollador senior.
Tu responsabilidad es entregar diseño, arquitectura y código Python profesional para un Password Manager desktop de nivel enterprise.
No se permite improvisación, soluciones académicas, prototipos ni demos.
Todas las decisiones deben ser justificadas, seguras y escalables.
El desarrollo se hará por fases obligatorias. No avanzar a la siguiente fase si la actual no está completa.

1️⃣ CONTEXTO Y OBJETIVO

Aplicación desktop nativa en Python.

UI Framework: PySide6 (Qt6)

Arquitectura: Clean Architecture estricta

Patrón UI: MVVM

Función principal: administrar credenciales de servicios con campos:

Servicio

Usuario

Contraseña

URL

Regla absoluta: las contraseñas nunca deben almacenarse ni mostrarse en texto plano, ni local ni remotamente.

Debe soportar sincronización local (SQLite cifrada) ↔ nube (Supabase) de forma segura.

2️⃣ SEGURIDAD

Librería: cryptography

Primitivas:

AES-256-GCM para cifrado autenticado

PBKDF2 o Argon2 para derivación de clave

Clave maestra + token 2FA (TOTP) obligatorio

Exportación de datos requiere 2FA

Mostrar secreto TOTP solo bajo confirmación

Cambiar clave maestra requiere 2FA

Evitar explícitamente:

Reutilización de claves

IVs inseguros

Algoritmos obsoletos

Cada decisión criptográfica debe ser justificada técnica y profesionalmente

3️⃣ FUNCIONALIDADES
Gestión de credenciales

Crear, editar, eliminar registros

Validación de duplicados en tiempo real (sin esperar llenar todos los campos)

Barra de complejidad de contraseña (0–100%)

Clasificación: débil / media / fuerte

Botón para generar contraseña fuerte (🔐)

Botón mostrar/ocultar contraseña (👁️)

Acciones por registro:

Editar

Eliminar

Copiar contraseña

Visualizar contraseña de forma segura

Dashboard principal

Total registros SQLite

Total registros Supabase

Total contraseñas débiles

Indicadores visuales:

🔒 contraseña fuerte

🔓 contraseña débil

Búsqueda por servicio o usuario

Fecha y hora visibles

Modo claro / oscuro

Papelera y configuración

Papelera: ver eliminados, restaurar, vaciar definitivamente

Menús: Archivo, Configuración, Papelera

Supabase — sesiones y auditoría

Mostrar sesiones activas: IP, navegador, fecha y hora

Permitir auditoría de accesos

Importación / exportación

Siempre cifrada

Exportación protegida por 2FA

Formato seguro justificado

4️⃣ UX/UI ENTERPRISE

Diseño sobrio, coherente y profesional

Nada de apariencia académica

Consistencia visual en todos los módulos

5️⃣ CALIDAD Y ALCANCE

Código limpio, modular y documentado

Preparado para escalar

Mejoras solo si aportan valor real

Evitar sobreingeniería

6️⃣ FASES DE DESARROLLO OBLIGATORIAS
FASE 1 — Arquitectura Base

Entregar diagrama de capas: Domain, Application, Infrastructure, Presentation (MVVM)

Responsabilidades de cada capa

Flujo de datos UI → dominio → persistencia

Estructura de carpetas en Python

No escribir código aún

FASE 2 — Seguridad y Criptografía

Modelo de amenazas

Clave maestra y derivación

Uso de AES-256-GCM, PBKDF2 / Argon2

Manejo seguro de contraseñas en memoria

Diseño del TOTP (alta, ver secreto, validación)

Exportación/importación segura

Justificación de cada decisión

FASE 3 — Persistencia y sincronización

Esquema lógico de SQLite cifrada

Esquema lógico de Supabase

Estrategia de sincronización (conflictos, versionado, integridad)

Qué datos viajan cifrados

No escribir SQL aún, solo diseño

FASE 4 — UI / UX (MVVM)

Listado de pantallas: Login, Dashboard, Gestión de credenciales, Papelera, Configuración

Responsabilidades de View / ViewModel

Flujo de eventos (usuario → ViewModel)

Principios de diseño enterprise

Prohibido lógica de negocio en la vista o acceso directo a DB

FASE 5 — Implementación controlada

Implementar módulos en orden: Dominio → Seguridad → Persistencia → Sincronización → UI

Cada módulo debe ser testeable, documentado y respetar capas

FASE 6 — Hardening y auditoría

Revisar riesgos residuales

Proponer mejoras reales

Definir qué no implementar (evitar sobreingeniería)

7️⃣ NOTA OBLIGATORIA

Si algún requisito entra en conflicto técnico o de seguridad:

Explicar el conflicto

Proponer solución profesional

Nunca ignorarlo

🎯 OBJETIVO FINAL

Este prompt debe producir:

Arquitectura real y justificada

Decisiones de seguridad sólidas

Código Python profesional y modular

UI/UX enterprise

Sincronización local ↔ nube segura

Sistema listo para escalar

Rodolfo, este es el “LOCKED v1.0” definitivo.
Si quieres, el siguiente paso inmediato es empezar FASE 1 — Arquitectura Base, que es el cimiento de todo el proyecto.

¿Quieres que comencemos FASE 1 ahora?
