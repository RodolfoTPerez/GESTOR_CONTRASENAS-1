-- ============================================================================
-- SCRIPT DE CREACIÓN DE BÓVEDA DE PRUEBA
-- ============================================================================
-- Generado automáticamente - NO editar manualmente
-- Fecha: 2026-01-22 22:44:51
-- ============================================================================

-- PASO 1: Crear bóveda de prueba "A"
-- ============================================================================

INSERT INTO vault_groups (vault_name, vault_master_key, max_users)
VALUES (
    'A',  -- Nombre de la bóveda
    '\\xf2413536f7c023e479ea167ddb7fd5bced1eadca0dc74da092647acf7cb274db',  -- vault_master_key (32 bytes)
    5  -- Máximo de usuarios
)
ON CONFLICT (vault_name) DO UPDATE 
SET vault_master_key = EXCLUDED.vault_master_key;

-- Obtener el ID de la bóveda recién creada
DO $$ 
DECLARE
    v_vault_id INTEGER;
BEGIN
    SELECT id INTO v_vault_id FROM vault_groups WHERE vault_name = 'A';
    RAISE NOTICE 'Vault ID de bóveda A: %', v_vault_id;
END $$;


-- PASO 2: Crear registros en vault_access
-- ============================================================================


-- Usuario: RODOLFO
INSERT INTO vault_access (user_id, vault_id, wrapped_master_key)
VALUES (
    1,  -- user_id de RODOLFO
    (SELECT id FROM vault_groups WHERE vault_name = 'A'),  -- vault_id
    '\\xc6dd8b1b5cf473df34aa183868f824fb268e943807db8f9c67dd2421cb565d9946323eabc27d48644a174a9bf2a3b3e65982d6b39c0a923d400c7d90'  -- wrapped_master_key
)
ON CONFLICT (user_id, vault_id) DO UPDATE
SET wrapped_master_key = EXCLUDED.wrapped_master_key;

-- Usuario: KIKI
INSERT INTO vault_access (user_id, vault_id, wrapped_master_key)
VALUES (
    15,  -- user_id de KIKI
    (SELECT id FROM vault_groups WHERE vault_name = 'A'),  -- vault_id
    '\\xd79366d0ec95c26a0965edf92aceafb7351d8101600a09ca380d0debb56f8cce6b04d47425c6e0f2e0f92179438f90980bcb6204cb13b44f0b917a69'  -- wrapped_master_key
)
ON CONFLICT (user_id, vault_id) DO UPDATE
SET wrapped_master_key = EXCLUDED.wrapped_master_key;


-- PASO 3: Actualizar tabla users con vault_id
-- ============================================================================


UPDATE users 
SET vault_id = (SELECT id FROM vault_groups WHERE vault_name = 'A')
WHERE id = 1;  -- RODOLFO

UPDATE users 
SET vault_id = (SELECT id FROM vault_groups WHERE vault_name = 'A')
WHERE id = 15;  -- KIKI


-- ============================================================================
-- VERIFICACIÓN
-- ============================================================================

-- Ver bóveda creada
SELECT * FROM vault_groups WHERE vault_name = 'A';

-- Ver accesos
SELECT va.id, va.user_id, u.username, va.vault_id, vg.vault_name
FROM vault_access va
JOIN users u ON va.user_id = u.id
JOIN vault_groups vg ON va.vault_id = vg.id
WHERE vg.vault_name = 'A';

-- Ver usuarios asignados
SELECT id, username, vault_id
FROM users
WHERE vault_id = (SELECT id FROM vault_groups WHERE vault_name = 'A');

-- ============================================================================
-- FIN DEL SCRIPT
-- ============================================================================
