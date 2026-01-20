"""
Migration: Add new fields to accounts table
- website
- phone
- email
- address
- tax_id
- notes
"""
import sqlite3
import os

# Path to database
DB_PATH = os.path.join(os.path.dirname(__file__), 'crm.db')

def migrate():
    print("=" * 70)
    print("🔄 MIGRACIÓN: Añadir campos a tabla accounts")
    print("=" * 70)
    
    print(f"\n📍 Buscando BD en: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print("❌ ERROR: La base de datos NO EXISTE")
        print("\n💡 SOLUCIONES:")
        print("   1. Ejecutar: python create_tables.py")
        print("   2. O arrancar el servidor para que se cree automáticamente")
        return False
    
    print(f"✅ Base de datos encontrada")
    print(f"📊 Tamaño: {os.path.getsize(DB_PATH) / 1024:.2f} KB")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if accounts table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts'")
    if not cursor.fetchone():
        print("\n❌ ERROR: La tabla 'accounts' NO EXISTE")
        print("\n💡 SOLUCIÓN:")
        print("   1. Ejecutar: python create_tables.py")
        print("   2. Reiniciar servidor")
        conn.close()
        return False
    
    print("✅ Tabla 'accounts' existe")
    
    # Check existing columns
    cursor.execute("PRAGMA table_info(accounts)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    print(f"\n📋 Columnas actuales ({len(existing_columns)}):")
    for col in existing_columns:
        print(f"   - {col}")
    
    # Add new columns if they don't exist
    new_columns = {
        'website': 'TEXT NULL',
        'phone': 'TEXT NULL',
        'email': 'TEXT NULL',
        'address': 'TEXT NULL',
        'tax_id': 'TEXT NULL',
        'notes': 'TEXT NULL'
    }
    
    print(f"\n🔧 Añadiendo campos nuevos...")
    added_count = 0
    
    for col_name, col_type in new_columns.items():
        if col_name not in existing_columns:
            try:
                sql = f"ALTER TABLE accounts ADD COLUMN {col_name} {col_type}"
                cursor.execute(sql)
                print(f"   ✅ Añadido: {col_name}")
                added_count += 1
            except sqlite3.OperationalError as e:
                print(f"   ⚠️  Error añadiendo {col_name}: {e}")
        else:
            print(f"   ℹ️  Ya existe: {col_name}")
    
    if added_count > 0:
        conn.commit()
        print(f"\n✅ Se añadieron {added_count} columnas nuevas")
    else:
        print(f"\n✅ Todas las columnas ya existían")
    
    # Verify final state
    print("\n🔍 Verificación final...")
    cursor.execute("PRAGMA table_info(accounts)")
    final_columns = [row[1] for row in cursor.fetchall()]
    
    print(f"\n📋 Columnas finales ({len(final_columns)}):")
    for col in final_columns:
        is_new = col in new_columns
        marker = "🆕" if is_new else "  "
        print(f"   {marker} {col}")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("✅ MIGRACIÓN COMPLETADA")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    success = migrate()
    if success:
        print("\n🚀 Siguiente paso: Reiniciar el servidor")
        print("   START_CRM.bat")
    else:
        print("\n⚠️  La migración no pudo completarse")
        print("   Revisar los mensajes de error arriba")

