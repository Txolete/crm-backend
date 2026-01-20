"""
DIAGNÓSTICO SQL PROFUNDO - Base de Datos
=========================================

Este script revisa DIRECTAMENTE la base de datos para ver qué está pasando.

Uso:
    python debug_database.py
"""

import sqlite3
import sys
from colorama import init, Fore, Style

init(autoreset=True)

DB_PATH = "crm.db"


def print_header(text):
    print("\n" + "=" * 80)
    print(f"{Fore.CYAN}{Style.BRIGHT}{text}")
    print("=" * 80)


def print_success(message):
    print(f"{Fore.GREEN}✅ {message}")


def print_error(message):
    print(f"{Fore.RED}❌ {message}")


def print_warning(message):
    print(f"{Fore.YELLOW}⚠️  {message}")


def print_info(message):
    print(f"{Fore.BLUE}ℹ️  {message}")


def check_database():
    """Verificar conexión a BD"""
    try:
        conn = sqlite3.connect(DB_PATH)
        print_success(f"Conectado a {DB_PATH}")
        return conn
    except Exception as e:
        print_error(f"No se puede conectar a {DB_PATH}: {e}")
        sys.exit(1)


def check_tasks_table_structure(conn):
    """Verificar estructura de tabla tasks"""
    print_header("ESTRUCTURA DE TABLA TASKS")
    
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(tasks)")
    columns = cursor.fetchall()
    
    print_info("Columnas en la tabla tasks:")
    
    expected_columns = [
        'id', 'opportunity_id', 'account_id', 'task_template_id',
        'title', 'description', 'due_date', 'priority', 'status',
        'assigned_to_user_id', 'completed_at', 'completed_by_user_id',
        'reminder_date', 'created_at', 'updated_at'
    ]
    
    found_columns = [col[1] for col in columns]
    
    for expected in expected_columns:
        if expected in found_columns:
            print_success(f"  {expected}")
        else:
            print_error(f"  {expected} - FALTA")
    
    # Verificar si opportunity_id es nullable
    for col in columns:
        if col[1] == 'opportunity_id':
            is_nullable = col[3] == 0  # notnull = 0 significa nullable
            if is_nullable:
                print_success("  opportunity_id es NULLABLE ✓")
            else:
                print_warning("  opportunity_id es NOT NULL")
    
    return found_columns


def check_tasks_data(conn):
    """Verificar datos en tasks"""
    print_header("DATOS EN TABLA TASKS")
    
    cursor = conn.cursor()
    
    # Contar tareas
    cursor.execute("SELECT COUNT(*) FROM tasks")
    total = cursor.fetchone()[0]
    print_info(f"Total de tareas: {total}")
    
    if total == 0:
        print_warning("No hay tareas en la BD")
        return
    
    # Ver primeras 3 tareas
    print_info("\nPrimeras 3 tareas:")
    cursor.execute("""
        SELECT 
            id, 
            title, 
            opportunity_id, 
            account_id, 
            assigned_to_user_id,
            status,
            priority
        FROM tasks 
        LIMIT 3
    """)
    
    tasks = cursor.fetchall()
    for task in tasks:
        print(f"\n{Fore.MAGENTA}  Tarea: {task[0][:12]}...")
        print(f"{Fore.BLUE}    title: {task[1]}")
        print(f"{Fore.BLUE}    opportunity_id: {task[2] or 'NULL'}")
        print(f"{Fore.BLUE}    account_id: {task[3] or 'NULL'}")
        print(f"{Fore.BLUE}    assigned_to_user_id: {task[4] or 'NULL'}")
        print(f"{Fore.BLUE}    status: {task[5]}")
        print(f"{Fore.BLUE}    priority: {task[6]}")


def check_opportunities_data(conn):
    """Verificar datos en opportunities"""
    print_header("DATOS EN TABLA OPPORTUNITIES")
    
    cursor = conn.cursor()
    
    # Contar oportunidades
    cursor.execute("SELECT COUNT(*) FROM opportunities")
    total = cursor.fetchone()[0]
    print_info(f"Total de oportunidades: {total}")
    
    if total == 0:
        print_error("¡No hay oportunidades en la BD!")
        return
    
    # Ver primeras 3 oportunidades
    print_info("\nPrimeras 3 oportunidades:")
    cursor.execute("""
        SELECT id, name, account_id 
        FROM opportunities 
        LIMIT 3
    """)
    
    opps = cursor.fetchall()
    for opp in opps:
        print(f"\n{Fore.MAGENTA}  Oportunidad: {opp[0][:12]}...")
        print(f"{Fore.BLUE}    name: {opp[1] or 'NULL'}")
        print(f"{Fore.BLUE}    account_id: {opp[2]}")


def check_accounts_data(conn):
    """Verificar datos en accounts"""
    print_header("DATOS EN TABLA ACCOUNTS")
    
    cursor = conn.cursor()
    
    # Contar cuentas
    cursor.execute("SELECT COUNT(*) FROM accounts")
    total = cursor.fetchone()[0]
    print_info(f"Total de cuentas: {total}")
    
    if total == 0:
        print_error("¡No hay cuentas en la BD!")
        return
    
    # Ver primeras 3 cuentas
    print_info("\nPrimeras 3 cuentas:")
    cursor.execute("""
        SELECT id, name 
        FROM accounts 
        LIMIT 3
    """)
    
    accounts = cursor.fetchall()
    for acc in accounts:
        print(f"\n{Fore.MAGENTA}  Cuenta: {acc[0][:12]}...")
        print(f"{Fore.BLUE}    name: {acc[1]}")


def check_users_data(conn):
    """Verificar datos en users"""
    print_header("DATOS EN TABLA USERS")
    
    cursor = conn.cursor()
    
    # Contar usuarios
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    print_info(f"Total de usuarios: {total}")
    
    if total == 0:
        print_error("¡No hay usuarios en la BD!")
        return
    
    # Ver usuarios
    cursor.execute("SELECT id, name, email, role FROM users")
    users = cursor.fetchall()
    
    print_info("\nUsuarios:")
    for user in users:
        print(f"  {Fore.MAGENTA}{user[1]} ({user[2]}) - {user[3]}")


def check_relationships(conn):
    """Verificar relaciones entre tablas"""
    print_header("VERIFICACIÓN DE RELACIONES")
    
    cursor = conn.cursor()
    
    # Tareas con opportunity_id que no existe
    print_info("\n1. Tareas con opportunity_id que NO existe:")
    cursor.execute("""
        SELECT t.id, t.title, t.opportunity_id
        FROM tasks t
        LEFT JOIN opportunities o ON t.opportunity_id = o.id
        WHERE t.opportunity_id IS NOT NULL
        AND o.id IS NULL
    """)
    
    orphan_tasks = cursor.fetchall()
    if orphan_tasks:
        print_error(f"  ¡{len(orphan_tasks)} tareas con opportunity_id huérfano!")
        for task in orphan_tasks[:3]:
            print(f"    {Fore.RED}Task {task[0][:12]}: {task[1]} → opp {task[2][:12]} (NO EXISTE)")
    else:
        print_success("  Todas las tareas tienen opportunity_id válido")
    
    # Tareas con account_id que no existe
    print_info("\n2. Tareas con account_id que NO existe:")
    cursor.execute("""
        SELECT t.id, t.title, t.account_id
        FROM tasks t
        LEFT JOIN accounts a ON t.account_id = a.id
        WHERE t.account_id IS NOT NULL
        AND a.id IS NULL
    """)
    
    orphan_account_tasks = cursor.fetchall()
    if orphan_account_tasks:
        print_error(f"  ¡{len(orphan_account_tasks)} tareas con account_id huérfano!")
        for task in orphan_account_tasks[:3]:
            print(f"    {Fore.RED}Task {task[0][:12]}: {task[1]} → acc {task[2][:12]} (NO EXISTE)")
    else:
        print_success("  Todas las tareas tienen account_id válido")
    
    # Tareas con assigned_to que no existe
    print_info("\n3. Tareas con assigned_to_user_id que NO existe:")
    cursor.execute("""
        SELECT t.id, t.title, t.assigned_to_user_id
        FROM tasks t
        LEFT JOIN users u ON t.assigned_to_user_id = u.id
        WHERE t.assigned_to_user_id IS NOT NULL
        AND u.id IS NULL
    """)
    
    orphan_user_tasks = cursor.fetchall()
    if orphan_user_tasks:
        print_error(f"  ¡{len(orphan_user_tasks)} tareas con assigned_to_user_id huérfano!")
        for task in orphan_user_tasks[:3]:
            print(f"    {Fore.RED}Task {task[0][:12]}: {task[1]} → user {task[2][:12]} (NO EXISTE)")
    else:
        print_success("  Todas las tareas tienen assigned_to_user_id válido")


def check_join_query(conn):
    """Verificar query con JOINs como hace el endpoint"""
    print_header("SIMULACIÓN DE QUERY DEL ENDPOINT")
    
    cursor = conn.cursor()
    
    print_info("Ejecutando query similar al endpoint...")
    
    cursor.execute("""
        SELECT 
            t.id,
            t.title,
            t.opportunity_id,
            o.name AS opportunity_name,
            t.account_id,
            a.name AS account_name,
            t.assigned_to_user_id,
            u.name AS assigned_to_name
        FROM tasks t
        LEFT JOIN opportunities o ON t.opportunity_id = o.id
        LEFT JOIN accounts a ON t.account_id = a.id
        LEFT JOIN users u ON t.assigned_to_user_id = u.id
        LIMIT 5
    """)
    
    results = cursor.fetchall()
    
    if not results:
        print_warning("Query no retornó resultados")
        return
    
    print_success(f"Query retornó {len(results)} resultados")
    
    for row in results:
        print(f"\n{Fore.MAGENTA}  Task: {row[0][:12]}")
        print(f"{Fore.BLUE}    title: {row[1]}")
        print(f"{Fore.BLUE}    opportunity_id: {row[2] or 'NULL'}")
        
        if row[2]:  # Tiene opportunity_id
            if row[3]:  # opportunity_name cargó
                print(f"{Fore.GREEN}    opportunity_name: {row[3]} ✓")
            else:
                print(f"{Fore.RED}    opportunity_name: NULL (pero opportunity_id existe!) ❌")
        
        print(f"{Fore.BLUE}    account_id: {row[4] or 'NULL'}")
        
        if row[4]:  # Tiene account_id
            if row[5]:  # account_name cargó
                print(f"{Fore.GREEN}    account_name: {row[5]} ✓")
            else:
                print(f"{Fore.RED}    account_name: NULL (pero account_id existe!) ❌")
        
        print(f"{Fore.BLUE}    assigned_to_user_id: {row[6] or 'NULL'}")
        
        if row[6]:  # Tiene assigned_to_user_id
            if row[7]:  # assigned_to_name cargó
                print(f"{Fore.GREEN}    assigned_to_name: {row[7]} ✓")
            else:
                print(f"{Fore.RED}    assigned_to_name: NULL (pero assigned_to_user_id existe!) ❌")


def main():
    print_header("🔍 DIAGNÓSTICO SQL PROFUNDO - BASE DE DATOS")
    print(f"{Fore.CYAN}Base de datos: {DB_PATH}")
    
    conn = check_database()
    
    try:
        check_tasks_table_structure(conn)
        check_tasks_data(conn)
        check_opportunities_data(conn)
        check_accounts_data(conn)
        check_users_data(conn)
        check_relationships(conn)
        check_join_query(conn)
        
        print_header("RESUMEN")
        print(f"\n{Fore.CYAN}Si el último test (SIMULACIÓN DE QUERY) muestra:")
        print(f"{Fore.GREEN}  ✅ opportunity_name con valor → El problema está en el código Python")
        print(f"{Fore.RED}  ❌ opportunity_name NULL → El problema está en la BD (relaciones rotas)")
        
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Diagnóstico interrumpido")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n{Fore.RED}Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
