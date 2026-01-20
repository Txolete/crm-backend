-- ============================================
-- MIGRACIÓN: Actualizar tabla tasks
-- Fecha: 2026-01-19
-- Versión: v0.7.0 - Sistema de Tareas
-- ============================================

-- Añadir columnas nuevas a la tabla tasks
-- NOTA: SQLite no soporta ADD COLUMN múltiple en una sola sentencia

-- 1. Añadir account_id (vinculación flexible a cuentas)
ALTER TABLE tasks ADD COLUMN account_id TEXT NULL;

-- 2. Añadir description (descripción larga opcional)
ALTER TABLE tasks ADD COLUMN description TEXT NULL;

-- 3. Añadir priority (alta/media/baja)
ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'medium';

-- 4. Añadir completed_at (fecha de completado)
ALTER TABLE tasks ADD COLUMN completed_at TEXT NULL;

-- 5. Añadir completed_by_user_id (quién completó)
ALTER TABLE tasks ADD COLUMN completed_by_user_id TEXT NULL;

-- 6. Añadir reminder_date (recordatorio)
ALTER TABLE tasks ADD COLUMN reminder_date TEXT NULL;

-- ============================================
-- VERIFICACIÓN POST-MIGRACIÓN
-- ============================================

-- Verificar estructura de la tabla
-- PRAGMA table_info(tasks);

-- Resultado esperado:
-- id, opportunity_id, task_template_id, title, due_date, status, 
-- assigned_to_user_id, created_at, updated_at,
-- account_id, description, priority, completed_at, completed_by_user_id, reminder_date

-- ============================================
-- NOTAS IMPORTANTES
-- ============================================

-- 1. VINCULACIÓN FLEXIBLE:
--    - opportunity_id puede ser NULL ahora
--    - account_id puede ser NULL
--    - La aplicación debe validar que al menos UNO esté presente

-- 2. HACER OPPORTUNITY_ID NULLABLE:
--    SQLite no permite modificar columnas existentes fácilmente
--    Alternativas:
--    a) Crear nueva tabla con estructura correcta y migrar datos
--    b) Mantener opportunity_id NOT NULL y siempre poner un valor dummy
--    c) Usar solo account_id cuando no hay oportunidad
--
--    DECISIÓN: Por simplicidad, mantenemos opportunity_id NOT NULL
--              y cuando la tarea sea solo de cuenta, ponemos opportunity_id = ''
--              O mejor: en la aplicación validamos que al menos uno esté presente

-- 3. PRIORIDADES VÁLIDAS:
--    - 'high' → Alta (rojo)
--    - 'medium' → Media (amarillo, por defecto)
--    - 'low' → Baja (verde)

-- 4. ESTADOS ACTUALIZADOS:
--    Actualmente: 'open', 'done', 'canceled'
--    Propuesto: 'open', 'in_progress', 'completed', 'cancelled'
--    
--    Migración de datos (si hay tareas existentes):
--    UPDATE tasks SET status = 'completed' WHERE status = 'done';
--    UPDATE tasks SET status = 'cancelled' WHERE status = 'canceled';

-- ============================================
-- ROLLBACK (si es necesario)
-- ============================================

-- SQLite no soporta DROP COLUMN
-- Para hacer rollback hay que:
-- 1. Crear tabla temporal sin las columnas nuevas
-- 2. Copiar datos
-- 3. Eliminar tabla original
-- 4. Renombrar tabla temporal
--
-- Guardar backup de crm.db antes de ejecutar esta migración

-- ============================================
-- FIN DE MIGRACIÓN
-- ============================================
