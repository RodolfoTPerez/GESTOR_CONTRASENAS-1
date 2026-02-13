# ⚙️ Vultrax Core // Arquitectura Técnica y Protocolos

Este documento profundiza en la ingeniería detrás de la protección de datos y la inteligencia del sistema.

---

## 1. Protocolo de Cifrado de Grado Militar

Vultrax Core no solo cifra los datos, sino que garantiza su integridad mediante **Cifrado Autenticado**.

### Derivación de Clave (KDF)
Usamos **PBKDF2-HMAC-SHA256**:
- **Salt**: 16 bytes generados aleatoriamente la primera vez.
- **Iteraciones**: 100,000 (resistencia contra ataques de fuerza bruta).
- **Resultado**: Una clave de 256 bits (32 bytes) que nunca toca el disco.

### Algoritmo AES-256-GCM
Cada registro se cifra de forma independiente:
1.  **Nonce (IV)**: 12 bytes únicos para cada cifrado.
2.  **Ciphertext**: El dato cifrado.
3.  **Tag de Autenticación**: 16 bytes que validan que el dato no ha sido modificado.

---

## 2. Motor de Sincronización (Ghost-Sync)

El `SyncManager` utiliza una estrategia de **"Local-First"**:
- **Prioridad Local**: Los cambios se guardan inmediatamente en SQLite para que la app sea rápida.
- **Espejo en la Nube**: Tras guardar localmente, se dispara un proceso en segundo plano (Ghost Sync) que sube el registro a Supabase.
- **Límites de Escalabilidad**: La sincronización de auditoría maneja lotes de hasta 500 registros para garantizar visibilidad sin degradar el rendimiento.
- **Privacidad**: Los registros marcados como `is_private=1` viajan cifrados con la **Master Key** del usuario.

### 🛡️ Validación de Identidad (UUID)
Para garantizar la integridad en la nube (Supabase RLS), el sistema valida mediante Regex que todos los `user_id` y `target_user` sean UUIDs válidos antes de la transmisión.

---

## 3. Prevención de Duplicados

Vultrax Core implementa una restricción de unicidad global a nivel de base de datos y UI:
- **Índice Único**: La tabla `secrets` cuenta con un índice `idx_unique_service` sobre la columna `service`.
- **Validación en Tiempo Real**: El `ServiceDialog` bloquea la creación de servicios existentes consultando el `SecretRepository` antes de permitir el guardado.

---

## 4. Inteligencia Heurística (HeuristicWorker)

El sistema puntúa tu seguridad en tiempo real mediante el `HeuristicWorker`.

| Factor | Impacto en el Score | Lógica |
| :--- | :--- | :--- |
| **Claves Débiles** | -15 puntos | Contraseñas con menos de 70% de complejidad. |
| **Reutilización** | -10 puntos | Detección de hashes idénticos en diferentes servicios. |
| **Expiración** | -10 puntos | Claves con más de 180 días sin cambios. |
| **Falta de MFA** | -20 puntos | Administradores sin segundo factor de autenticación activo. |
| **Ataques Brutos** | -10 puntos | Más de 10 fallos de login en las últimas 24 horas. |

---

## 5. Esquema de Base de Datos (Estructura)

### Tabla `secrets`
- `id`: UUID único.
- `service`: Nombre del sitio (Clave Única Global).
- `username`: Cuenta de usuario.
- `secret`: Contraseña (siempre cifrada).
- `owner_name`: Nombre del usuario dueño.
- `is_private`: 1 para personal, 0 para compartido.

---

## 6. Simbiosis de Datos (Zero-Knowledge Sync Workflow)

Vultrax Core orquestra la confianza mediante una división estricta de responsabilidades entre el PC local y la nube:

### A. Nivel Local: El Búnker (SQLite)
*   **Aislamiento de Identidad:** Cada usuario posee su propio archivo `vault_*.db`.
*   **Preservación de Llaves:** El sistema prioriza las llaves y "Salts" locales. Mediante **HWID Binding**, los datos quedan ligados al hardware del equipo, impidiendo que una base de datos robada sea abierta en otra máquina incluso con la contraseña correcta.
*   **Cifrado en Origen:** Todo dato (secreto, nota o log) se cifra en la RAM antes de tocar el disco o salir hacia el `SyncManager`.

### B. Nivel Nube: El Espejo Blindado (Supabase)
*   **Zero-Knowledge Host:** Supabase actúa como un almacén de "ruido cifrado". Nunca recibe llaves maestras ni texto plano.
*   **Validación de Integridad:** El sistema valida los datos (ej. formato UUID) antes de la transmisión para evitar errores en la API de la nube.
*   **RLS & Filtrado de Operador:** Las políticas de Row Level Security aseguran que un usuario solo acceda a sus paquetes cifrados, manteniendo la privacidad absoluta entre inquilinos.

### C. Flujo Operativo (Ghost Sync)
1.  **Local-First:** Escritura inmediata en SQLite para latencia cero.
2.  **Validación Pre-Vuelo:** Verificación de esquemas y tipos de datos (Audit Push).
3.  **Sincronización Asíncrona:** El proceso de fondo sube los cambios sin interferir con la navegación del usuario.

---

> [!CAUTION]
> **Seguridad de Memoria**: Vultrax Core intenta limpiar las variables que contienen texto plano lo antes posible, pero se recomienda no dejar la aplicación abierta y desbloqueada si te alejas del equipo.
