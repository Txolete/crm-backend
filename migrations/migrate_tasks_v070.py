"""
Migración: Actualizar tabla tasks para Sistema de Tareas v0.7.0

Este script:
1. Hace backup de la BD
2. Añade columnas nuevas a tasks
3. Hace opportunity_id nullable (recreando tabla)
4. Migra datos de status antiguo a nuevo
5. Verifica que todo funcionó

Uso:
    python migrations/migrate_tasks_v070.py
"""

import sqlite3
import os
import shutil
from datetime import datetime


DB_PATH = "crm.db"
BACKUP_DIR = "data/backups"


def make_backup():
    """Crear backup antes de migrar"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"crm_pre_migration_{timestamp}.db")
    
    shutil.copy2(DB_PATH, backup_path)
    print(f"✅ Backup creado: {backup_path}")
    return backup_path


def execute_migration(conn):
    """Ejecutar migración de tasks"""
    cursor = conn.cursor()
    
    print("📋 Iniciando migración...")
    
    # 1. Verificar si las columnas ya existen
    cursor.execute("PRAGMA table_info(tasks)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'account_id' in columns:
        print("⚠️  Las columnas nuevas ya existen. Migración ya aplicada.")
        return False
    
    # 2. Crear tabla temporal con nueva estructura
    print("🔨 Creando tabla temporal...")
    cursor.execute("""
        CREATE TABLE tasks_new (
            id TEXT PRIMARY KEY,
            opportunity_id TEXT NULL,
            account_id TEXT NULL,
            task_template_id TEXT NULL,
            title TEXT NOT NULL,
            description TEXT NULL,
            due_date TEXT NULL,
            priority TEXT NOT NULL DEFAULT 'medium',
            status TEXT NOT NULL DEFAULT 'open',
            assigned_to_user_id TEXT NULL,
            completed_at TEXT NULL,
            completed_by_user_id TEXT NULL,
            reminder_date TEXT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            CHECK (status IN ('open', 'in_progress', 'completed', 'cancelled')),
            CHECK (priority IN ('high', 'medium', 'low')),
            CHECK (opportunity_id IS NOT NULL OR account_id IS NOT NULL),
            FOREIGN KEY(opportunity_id) REFERENCES opportunities(id),
            FOREIGN KEY(account_id) REFERENCES accounts(id),
            FOREIGN KEY(task_template_id) REFERENCES cfg_task_templates(id),
            FOREIGN KEY(assigned_to_user_id) REFERENCES users(id),
            FOREIGN KEY(completed_by_user_id) REFERENCES users(id)
        )
    """)
    
    # 3. Copiar datos existentes, mapeando status antiguo → nuevo
    print("📦 Migrando datos...")
    cursor.execute("""
        INSERT INTO tasks_new 
            (id, opportunity_id, task_template_id, title, due_date, 
             status, assigned_to_user_id, created_at, updated_at)
        SELECT 
            id, opportunity_id, task_template_id, title, due_date,
            CASE 
                WHEN status = 'done' THEN 'completed'
                WHEN status = 'canceled' THEN 'cancelled'
                ELSE status
            END as status,
            assigned_to_user_id, created_at, updated_at
        FROM tasks
    """)
    
    rows_migrated = cursor.rowcount
    print(f"✅ {rows_migrated} tareas migradas")
    
    # 4. Eliminar tabla antigua
    print("🗑️  Eliminando tabla antigua...")
    cursor.execute("DROP TABLE tasks")
    
    # 5. Renombrar tabla nueva
    print("♻️  Renombrando tabla nueva...")
    cursor.execute("ALTER TABLE tasks_new RENAME TO tasks")
    
    # 6. Verificar estructura final
    cursor.execute("PRAGMA table_info(tasks)")
    final_columns = [row[1] for row in cursor.fetchall()]
    
    expected_columns = [
        'id', 'opportunity_id', 'account_id', 'task_template_id',
        'title', 'description', 'due_date', 'priority', 'status',
        'assigned_to_user_id', 'completed_at', 'completed_by_user_id',
        'reminder_date', 'created_at', 'updated_at'
    ]
    
    print("\n📊 Verificación de columnas:")
    for col in expected_columns:
        if col in final_columns:
            print(f"  ✅ {col}")
        else:
            print(f"  ❌ {col} - FALTA")
    
    return True


def main():
    print("=" * 60)
    print("MIGRACIÓN: Sistema de Tareas v0.7.0")
    print("=" * 60)
    print()
    
    # Verificar que existe la BD
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: No se encuentra {DB_PATH}")
        print("   Ejecuta este script desde la raíz del proyecto")
        return
    
    # Crear backup
    backup_path = make_backup()
    
    # Conectar y migrar
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Ejecutar migración
        migrated = execute_migration(conn)
        
        if migrated:
            # Commit
            conn.commit()
            print("\n✅ Migración completada exitosamente")
            print(f"💾 Backup guardado en: {backup_path}")
            print("\n📝 Cambios aplicados:")
            print("  - opportunity_id ahora es nullable")
            print("  - Añadido account_id (vinculación a cuentas)")
            print("  - Añadido description (texto largo)")
            print("  - Añadido priority (high/medium/low)")
            print("  - Añadido completed_at, completed_by_user_id")
            print("  - Añadido reminder_date")
            print("  - Estados actualizados: open, in_progress, completed, cancelled")
        else:
            print("\n⚠️  No se realizó migración (ya aplicada)")
        
    except Exception as e:
        print(f"\n❌ Error durante la migración: {e}")
        print(f"💾 Para restaurar, copia el backup: {backup_path}")
        raise
    
    finally:
        conn.close()
    
    print("\n" + "=" * 60)
    print("Migración finalizada")
    print("=" * 60)


if __name__ == "__main__":
    main()
