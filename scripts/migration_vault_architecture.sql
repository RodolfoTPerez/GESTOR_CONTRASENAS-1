-- ============================================================================
-- SCRIPT DE MIGRACIÓN: ARQUITECTURA MULTI-BÓVEDA CON KEY WRAPPING
-- ============================================================================
-- Fecha: 2026-01-22
-- Objetivo: Implementar sistema de bóvedas compartidas para resolver error de llave
-- Base de datos: PostgreSQL (Supabase)
-- ============================================================================

-- ==========================
-- PASO 1: CREAR NUEVA TABLA vault_groups
-- ==========================

CREATE TABLE IF NOT EXISTS vault_groups (
    id SERIAL PRIMARY KEY,
    vault_name TEXT UNIQUE NOT NULL,
    vault_master_key BYTEA NOT NULL,  -- Llave AES-256 (32 bytes) compartida por todos los usuarios de esta bóveda
    max_users INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índice para búsqueda rápida por nombre
CREATE INDEX idx_vault_groups_name ON vault_groups(vault_name);

-- Comentarios
COMMENT ON TABLE vault_groups IS 'Bóvedas de equipos. Cada bóveda tiene su propia master key compartida.';
COMMENT ON COLUMN vault_groups.vault_master_key IS 'Llave AES-256 (32 bytes) usada para encriptar todos los servicios de esta bóveda';
COMMENT ON COLUMN vault_groups.max_users IS 'Número máximo de usuarios permitidos en esta bóveda';

-- ==========================
-- PASO 2: CREAR NUEVA TABLA vault_access
-- ==========================

CREATE TABLE IF NOT EXISTS vault_access (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,  -- Referencia a users.id
    vault_id INTEGER NOT NULL REFERENCES vault_groups(id) ON DELETE CASCADE,
    wrapped_master_key BYTEA NOT NULL,  -- vault_master_key encriptada con KEK del usuario
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, vault_id)
);

-- Índices para búsquedas rápidas
CREATE INDEX idx_vault_access_user ON vault_access(user_id);
CREATE INDEX idx_vault_access_vault ON vault_access(vault_id);

-- Comentarios
COMMENT ON TABLE vault_access IS 'Control de acceso a bóvedas. Cada usuario tiene su copia encriptada de la vault_master_key.';
COMMENT ON COLUMN vault_access.wrapped_master_key IS 'vault_master_key encriptada con la KEK del usuario (derivada de su password)';

-- ==========================
-- PASO 3: MODIFICAR TABLA users
-- ==========================

-- Agregar columna vault_id si no existe
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'vault_id'
    ) THEN
        ALTER TABLE users ADD COLUMN vault_id INTEGER REFERENCES vault_groups(id) ON DELETE SET NULL;
        CREATE INDEX idx_users_vault ON users(vault_id);
    END IF;
END $$;

COMMENT ON COLUMN users.vault_id IS 'Bóveda a la que pertenece este usuario';

-- ==========================
-- PASO 4: MODIFICAR TABLA secrets
-- ==========================

-- Agregar columna vault_id si no existe
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'secrets' AND column_name = 'vault_id'
    ) THEN
        ALTER TABLE secrets ADD COLUMN vault_id INTEGER REFERENCES vault_groups(id) ON DELETE CASCADE;
        CREATE INDEX idx_secrets_vault ON secrets(vault_id);
    END IF;
END $$;

COMMENT ON COLUMN secrets.vault_id IS 'Bóveda a la que pertenece este servicio';

-- ==========================
-- PASO 5: ROW LEVEL SECURITY (RLS)
-- ==========================

-- Habilitar RLS en todas las tablas
ALTER TABLE vault_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE vault_access ENABLE ROW LEVEL SECURITY;

-- Política para vault_groups: Solo lectura para usuarios autenticados
CREATE POLICY vault_groups_select_policy ON vault_groups
    FOR SELECT
    USING (true);  -- Todos pueden leer (pero no la master_key, eso lo filtramos en código)

-- Política para vault_access: Solo puede ver sus propios registros
CREATE POLICY vault_access_select_policy ON vault_access
    FOR SELECT
    USING (user_id = current_setting('app.current_user_id')::INTEGER);

-- Política para users: Solo ve usuarios de su misma bóveda
CREATE POLICY users_vault_isolation ON users
    FOR SELECT
    USING (vault_id = current_setting('app.current_vault_id')::INTEGER OR vault_id IS NULL);

-- Política para secrets: Solo ve servicios de su bóveda
CREATE POLICY secrets_vault_isolation ON secrets
    FOR SELECT
    USING (vault_id = current_setting('app.current_vault_id')::INTEGER OR vault_id IS NULL);

-- ==========================
-- PASO 6: DATOS DE EJEMPLO (OPCIONAL - SOLO PARA TESTING)
-- ==========================

-- Crear bóveda de ejemplo A
-- NOTA: En producción, esto lo hará la aplicación Python
/*
INSERT INTO vault_groups (vault_name, vault_master_key, max_users)
VALUES ('A', gen_random_bytes(32), 5);

-- Crear bóveda de ejemplo B
INSERT INTO vault_groups (vault_name, vault_master_key, max_users)
VALUES ('B', gen_random_bytes(32), 5);

-- Crear bóveda de ejemplo C
INSERT INTO vault_groups (vault_name, vault_master_key, max_users)
VALUES ('C', gen_random_bytes(32), 3);
*/

-- ==========================
-- PASO 7: FUNCIONES AUXILIARES
-- ==========================

-- Función para obtener el número de usuarios en una bóveda
CREATE OR REPLACE FUNCTION get_vault_user_count(p_vault_id INTEGER)
RETURNS INTEGER AS $$
BEGIN
    RETURN (SELECT COUNT(*) FROM users WHERE vault_id = p_vault_id);
END;
$$ LANGUAGE plpgsql;

-- Función para verificar si una bóveda está llena
CREATE OR REPLACE FUNCTION is_vault_full(p_vault_id INTEGER)
RETURNS BOOLEAN AS $$
DECLARE
    v_max_users INTEGER;
    v_current_users INTEGER;
BEGIN
    SELECT max_users INTO v_max_users FROM vault_groups WHERE id = p_vault_id;
    SELECT get_vault_user_count(p_vault_id) INTO v_current_users;
    RETURN v_current_users >= v_max_users;
END;
$$ LANGUAGE plpgsql;

-- ==========================
-- VERIFICACIÓN FINAL
-- ==========================

-- Mostrar resumen de tablas creadas
SELECT 
    'vault_groups' AS table_name,
    COUNT(*) AS record_count
FROM vault_groups
UNION ALL
SELECT 
    'vault_access',
    COUNT(*)
FROM vault_access
UNION ALL
SELECT 
    'users (with vault_id)',
    COUNT(*)
FROM users WHERE vault_id IS NOT NULL;

-- ==========================
-- ROLLBACK (En caso de error)
-- ==========================

-- Para deshacer todos los cambios, ejecutar:
/*
DROP POLICY IF EXISTS secrets_vault_isolation ON secrets;
DROP POLICY IF EXISTS users_vault_isolation ON users;
DROP POLICY IF EXISTS vault_access_select_policy ON vault_access;
DROP POLICY IF EXISTS vault_groups_select_policy ON vault_groups;

DROP FUNCTION IF EXISTS is_vault_full(INTEGER);
DROP FUNCTION IF EXISTS get_vault_user_count(INTEGER);

ALTER TABLE secrets DROP COLUMN IF EXISTS vault_id;
ALTER TABLE users DROP COLUMN IF EXISTS vault_id;

DROP TABLE IF EXISTS vault_access;
DROP TABLE IF EXISTS vault_groups;
*/

-- ============================================================================
-- FIN DEL SCRIPT
-- ============================================================================
