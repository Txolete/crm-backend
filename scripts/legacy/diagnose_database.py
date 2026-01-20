"""
DIAGNÓSTICO COMPLETO DE LA BASE DE DATOS
Verifica estructura, datos y problemas
"""
import sqlite3
import os
from datetime import datetime

# Path to database
DB_PATH = os.path.join(os.path.dirname(__file__), 'crm.db')

def main():
    print("=" * 70)
    print("🔍 DIAGNÓSTICO COMPLETO DE LA BASE DE DATOS")
    print("=" * 70)
    print(f"\n📍 Ruta BD: {DB_PATH}")
    print(f"📍 Existe: {os.path.exists(DB_PATH)}")
    
    if not os.path.exists(DB_PATH):
        print("\n❌ ERROR: La base de datos NO EXISTE")
        print("\n💡 SOLUCIÓN: Arrancar el servidor para que se cree automáticamente")
        return
    
    print(f"📍 Tamaño: {os.path.getsize(DB_PATH) / 1024:.2f} KB")
    print(f"📍 Última modificación: {datetime.fromtimestamp(os.path.getmtime(DB_PATH))}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all tables
    print("\n" + "=" * 70)
    print("📊 TABLAS EN LA BASE DE DATOS")
    print("=" * 70)
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    if not tables:
        print("❌ NO HAY TABLAS EN LA BASE DE DATOS")
        conn.close()
        return
    
    print(f"\n✅ Total de tablas: {len(tables)}\n")
    
    for (table_name,) in tables:
        print(f"\n{'─' * 70}")
        print(f"📋 Tabla: {table_name}")
        print(f"{'─' * 70}")
        
        # Get columns
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        print(f"   Columnas ({len(columns)}):")
        for col in columns:
            col_id, col_name, col_type, not_null, default_val, pk = col
            pk_mark = " 🔑" if pk else ""
            null_mark = " NOT NULL" if not_null else ""
            default_mark = f" DEFAULT {default_val}" if default_val else ""
            print(f"      - {col_name}: {col_type}{pk_mark}{null_mark}{default_mark}")
        
        # Count records
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   Registros: {count}")
            
            if count > 0 and table_name in ['accounts', 'opportunities', 'contacts']:
                # Show sample
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
                sample = cursor.fetchone()
                if sample:
                    print(f"   Muestra del primer registro:")
                    col_names = [c[1] for c in columns]
                    for i, val in enumerate(sample):
                        if val is not None:
                            display_val = str(val)[:50] + "..." if len(str(val)) > 50 else val
                            print(f"      {col_names[i]}: {display_val}")
        except Exception as e:
            print(f"   ⚠️  Error contando registros: {e}")
    
    # CRITICAL CHECKS
    print("\n" + "=" * 70)
    print("🔍 VERIFICACIONES CRÍTICAS")
    print("=" * 70)
    
    table_names = [t[0] for t in tables]
    
    required_tables = {
        'users': 'Usuarios del sistema',
        'accounts': 'Clientes/empresas',
        'opportunities': 'Oportunidades',
        'contacts': 'Contactos',
        'contact_channels': 'Emails/teléfonos',
        'cfg_stages': 'Etapas del pipeline',
        'cfg_regions': 'Regiones/provincias',
        'cfg_customer_types': 'Tipos de cliente',
        'cfg_lead_sources': 'Fuentes de leads'
    }
    
    print("\n✅ Tablas requeridas:")
    missing_tables = []
    for table, desc in required_tables.items():
        if table in table_names:
            print(f"   ✅ {table:25} - {desc}")
        else:
            print(f"   ❌ {table:25} - {desc} [FALTA]")
            missing_tables.append(table)
    
    if missing_tables:
        print(f"\n⚠️  ADVERTENCIA: Faltan {len(missing_tables)} tablas críticas")
        print("   Esto causará errores al arrancar el servidor")
    
    # Check accounts table structure if exists
    if 'accounts' in table_names:
        print("\n" + "=" * 70)
        print("🔍 VERIFICACIÓN DETALLADA: TABLA ACCOUNTS")
        print("=" * 70)
        
        cursor.execute("PRAGMA table_info(accounts)")
        acc_columns = [col[1] for col in cursor.fetchall()]
        
        required_columns = [
            'id', 'name', 'website', 'phone', 'email', 'address', 'tax_id',
            'region_id', 'customer_type_id', 'lead_source_id', 'owner_user_id',
            'status', 'notes', 'created_at', 'updated_at'
        ]
        
        print("\n✅ Columnas esperadas:")
        missing_columns = []
        for col in required_columns:
            if col in acc_columns:
                print(f"   ✅ {col}")
            else:
                print(f"   ❌ {col} [FALTA]")
                missing_columns.append(col)
        
        if missing_columns:
            print(f"\n⚠️  ADVERTENCIA: Faltan {len(missing_columns)} columnas en accounts")
            print("   Ejecutar: python repair_database.py")
    
    # Check opportunities
    if 'opportunities' in table_names:
        cursor.execute("SELECT COUNT(*) FROM opportunities WHERE status='active'")
        opp_count = cursor.fetchone()[0]
        print(f"\n📊 Oportunidades activas: {opp_count}")
        
        if opp_count == 0:
            print("   ⚠️  No hay oportunidades activas (Kanban estará vacío)")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("✅ DIAGNÓSTICO COMPLETADO")
    print("=" * 70)
    
    if missing_tables:
        print("\n⚠️  ACCIÓN REQUERIDA:")
        print("   1. Ejecutar: python create_tables.py")
        print("   2. Reiniciar servidor")
    elif 'accounts' in table_names and missing_columns:
        print("\n⚠️  ACCIÓN REQUERIDA:")
        print("   1. Ejecutar: python repair_database.py")
        print("   2. Reiniciar servidor")

if __name__ == "__main__":
    main()
