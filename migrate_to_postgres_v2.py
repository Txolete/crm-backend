"""
Script para migrar datos de SQLite a PostgreSQL - VERSIÓN CORREGIDA
"""
import sqlite3
import psycopg2
from psycopg2 import sql
import os

def migrate_sqlite_to_postgres(sqlite_path, postgres_url):
    """
    Migra datos de SQLite a PostgreSQL
    
    Args:
        sqlite_path: Ruta al archivo SQLite (ej: 'crm.db')
        postgres_url: URL de conexión PostgreSQL de Railway
    """
    print("🔄 Iniciando migración SQLite → PostgreSQL...")
    
    # Conectar a SQLite
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # Conectar a PostgreSQL
    if postgres_url.startswith("postgres://"):
        postgres_url = postgres_url.replace("postgres://", "postgresql://", 1)
    
    pg_conn = psycopg2.connect(postgres_url)
    pg_cursor = pg_conn.cursor()
    
    # Deshabilitar foreign keys temporalmente
    pg_cursor.execute("SET session_replication_role = 'replica';")
    
    # Lista de tablas a migrar (en orden correcto)
    tables = [
        'users',
        'cfg_regions',
        'cfg_customer_types',
        'cfg_lead_sources',
        'cfg_contact_roles',
        'cfg_task_templates',
        'cfg_stages',
        'cfg_stage_probabilities',
        'targets',
        'accounts',
        'contacts',
        'contact_channels',
        'opportunities',
        'tasks',
        'activities',
        'audit_log',
        'app_versions'
    ]
    
    migrated_count = 0
    
    for table in tables:
        try:
            # Obtener datos de SQLite
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                print(f"  ⏭️  {table}: Sin datos")
                continue
            
            # Obtener nombres de columnas
            columns = [description[0] for description in sqlite_cursor.description]
            
            # Limpiar tabla en PostgreSQL primero
            pg_cursor.execute(f"DELETE FROM {table}")
            
            # Insertar datos uno por uno (más seguro)
            for row in rows:
                row_dict = dict(row)
                values = [row_dict[col] for col in columns]
                
                # Construir query con placeholders seguros
                placeholders = ','.join(['%s'] * len(columns))
                columns_str = ','.join([f'"{col}"' for col in columns])
                insert_query = f'INSERT INTO {table} ({columns_str}) VALUES ({placeholders})'
                
                pg_cursor.execute(insert_query, values)
            
            pg_conn.commit()
            migrated_count += len(rows)
            print(f"  ✅ {table}: {len(rows)} registros migrados")
            
        except Exception as e:
            print(f"  ❌ {table}: Error - {e}")
            pg_conn.rollback()
            continue
    
    # Rehabilitar foreign keys
    pg_cursor.execute("SET session_replication_role = 'origin';")
    pg_conn.commit()
    
    # Cerrar conexiones
    sqlite_conn.close()
    pg_conn.close()
    
    print(f"\n✅ Migración completada: {migrated_count} registros totales")
    print("⚠️  IMPORTANTE: Verifica los datos en PostgreSQL")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("Uso: python migrate_to_postgres_v2.py <sqlite_path> <postgres_url>")
        print("Ejemplo: python migrate_to_postgres_v2.py crm.db postgresql://user:pass@host:5432/db")
        sys.exit(1)
    
    sqlite_path = sys.argv[1]
    postgres_url = sys.argv[2]
    
    if not os.path.exists(sqlite_path):
        print(f"❌ Error: No se encuentra el archivo {sqlite_path}")
        sys.exit(1)
    
    confirm = input(f"¿Migrar datos de {sqlite_path} a PostgreSQL? (sí/no): ")
    if confirm.lower() in ['sí', 'si', 'yes', 's', 'y']:
        migrate_sqlite_to_postgres(sqlite_path, postgres_url)
    else:
        print("❌ Migración cancelada")
