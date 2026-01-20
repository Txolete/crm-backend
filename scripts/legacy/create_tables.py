"""
CREAR/REPARAR TODAS LAS TABLAS DE LA BASE DE DATOS
Ejecuta el SQL completo de la SPEC
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'crm.db')

# SQL completo de la SPEC (compatible SQLite/PostgreSQL)
SQL_SCHEMA = """
-- === USERS ===
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin','sales','viewer')),
    is_active INTEGER NOT NULL DEFAULT 1,
    last_login_at TEXT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- === CONFIG ===
CREATE TABLE IF NOT EXISTS cfg_regions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    country_code TEXT NOT NULL DEFAULT 'ES',
    is_active INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cfg_customer_types (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    is_active INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cfg_lead_sources (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    category TEXT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cfg_contact_roles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    is_active INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cfg_task_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    default_due_days INTEGER NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cfg_stages (
    id TEXT PRIMARY KEY,
    key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('open','won','lost')),
    is_terminal INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cfg_stage_probabilities (
    stage_id TEXT PRIMARY KEY,
    probability REAL NOT NULL CHECK (probability BETWEEN 0 AND 1),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(stage_id) REFERENCES cfg_stages(id)
);

-- === TARGETS ===
CREATE TABLE IF NOT EXISTS targets (
    id TEXT PRIMARY KEY,
    year INTEGER NOT NULL,
    target_pipeline_total REAL NOT NULL,
    target_pipeline_weighted REAL NOT NULL,
    target_closed REAL NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- === ACCOUNTS / CONTACTS ===
CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    
    -- Contact info (NUEVO)
    website TEXT NULL,
    phone TEXT NULL,
    email TEXT NULL,
    address TEXT NULL,
    
    -- Legal/fiscal (NUEVO)
    tax_id TEXT NULL,
    
    -- Classification
    region_id TEXT NULL,
    region_other_text TEXT NULL,
    customer_type_id TEXT NULL,
    customer_type_other_text TEXT NULL,
    lead_source_id TEXT NULL,
    lead_source_detail TEXT NULL,
    
    -- Management
    owner_user_id TEXT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    
    -- Notes (NUEVO)
    notes TEXT NULL,
    
    -- Audit
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contacts (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    first_name TEXT NULL,
    last_name TEXT NULL,
    contact_role_id TEXT NULL,
    contact_role_other_text TEXT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contact_channels (
    id TEXT PRIMARY KEY,
    contact_id TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('email','phone')),
    value TEXT NOT NULL,
    is_primary INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

-- === OPPORTUNITIES ===
CREATE TABLE IF NOT EXISTS opportunities (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    name TEXT NULL,
    stage_id TEXT NOT NULL,
    stage_detail TEXT NULL,
    expected_value_eur REAL NOT NULL,
    weighted_value_override_eur REAL NULL,
    probability_override REAL NULL,
    forecast_close_month TEXT NULL,
    close_outcome TEXT NOT NULL DEFAULT 'open',
    close_date TEXT NULL,
    won_value_eur REAL NULL,
    lost_reason TEXT NULL,
    owner_user_id TEXT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- === TASKS / ACTIVITIES ===
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    opportunity_id TEXT NOT NULL,
    task_template_id TEXT NULL,
    title TEXT NOT NULL,
    due_date TEXT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    assigned_to_user_id TEXT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS activities (
    id TEXT PRIMARY KEY,
    opportunity_id TEXT NOT NULL,
    type TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    summary TEXT NOT NULL,
    created_by_user_id TEXT NULL,
    created_at TEXT NOT NULL
);

-- === AUDIT / VERSIONS ===
CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    entity TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL,
    before_json TEXT NULL,
    after_json TEXT NULL,
    user_id TEXT NULL,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS app_versions (
    id TEXT PRIMARY KEY,
    version TEXT NOT NULL UNIQUE,
    release_date TEXT NOT NULL,
    title TEXT NOT NULL,
    changes_markdown TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

def main():
    print("=" * 70)
    print("🔧 CREAR/REPARAR BASE DE DATOS")
    print("=" * 70)
    
    print(f"\n📍 Ruta BD: {DB_PATH}")
    print(f"📍 Existe: {os.path.exists(DB_PATH)}")
    
    if os.path.exists(DB_PATH):
        size_kb = os.path.getsize(DB_PATH) / 1024
        print(f"📍 Tamaño actual: {size_kb:.2f} KB")
        
        respuesta = input("\n⚠️  La base de datos existe. ¿Crear tablas faltantes? (s/n): ")
        if respuesta.lower() != 's':
            print("❌ Operación cancelada")
            return
    else:
        print("\n✅ Creando nueva base de datos...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n📝 Ejecutando SQL schema...")
    
    try:
        # Execute all CREATE TABLE statements
        cursor.executescript(SQL_SCHEMA)
        conn.commit()
        print("✅ Todas las tablas creadas/verificadas")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        conn.close()
        return
    
    # Verify tables
    print("\n🔍 Verificando tablas creadas...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [t[0] for t in cursor.fetchall()]
    
    print(f"✅ Total tablas: {len(tables)}")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   - {table:25} ({count} registros)")
    
    # Check accounts columns
    print("\n🔍 Verificando columnas de accounts...")
    cursor.execute("PRAGMA table_info(accounts)")
    columns = [col[1] for col in cursor.fetchall()]
    
    new_columns = ['website', 'phone', 'email', 'address', 'tax_id', 'notes']
    for col in new_columns:
        if col in columns:
            print(f"   ✅ {col}")
        else:
            print(f"   ❌ {col} [FALTA - necesita migración]")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("✅ PROCESO COMPLETADO")
    print("=" * 70)
    print("\nAcciones siguientes:")
    print("1. Si faltan columnas en accounts: python migrate_accounts_fields.py")
    print("2. Reiniciar servidor: START_CRM.bat")

if __name__ == "__main__":
    main()
