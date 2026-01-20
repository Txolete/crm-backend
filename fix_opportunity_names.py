"""
REPARAR NOMBRES DE OPORTUNIDADES
=================================

Este script asigna nombres a todas las oportunidades que tienen name = NULL
basándose en el nombre de la cuenta asociada.

Formato: "[Nombre Cuenta] - Oportunidad"

Uso:
    python fix_opportunity_names.py
"""

import sqlite3
import sys
from colorama import init, Fore, Style
from datetime import datetime

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


def backup_database():
    """Crear backup de la BD antes de modificar"""
    print_header("BACKUP DE BASE DE DATOS")
    
    import shutil
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"crm_backup_{timestamp}.db"
    
    try:
        shutil.copy2(DB_PATH, backup_path)
        print_success(f"Backup creado: {backup_path}")
        return backup_path
    except Exception as e:
        print_error(f"Error al crear backup: {e}")
        sys.exit(1)


def get_opportunities_without_name(conn):
    """Obtener oportunidades sin nombre"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            o.id,
            o.account_id,
            a.name AS account_name,
            o.expected_value_eur,
            o.stage_id
        FROM opportunities o
        JOIN accounts a ON o.account_id = a.id
        WHERE o.name IS NULL OR o.name = ''
        ORDER BY a.name
    """)
    
    return cursor.fetchall()


def update_opportunity_name(conn, opp_id, new_name):
    """Actualizar nombre de oportunidad"""
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    
    cursor.execute("""
        UPDATE opportunities 
        SET name = ?, updated_at = ?
        WHERE id = ?
    """, (new_name, timestamp, opp_id))


def main():
    print_header("🔧 REPARAR NOMBRES DE OPORTUNIDADES")
    print(f"{Fore.CYAN}Base de datos: {DB_PATH}")
    print(f"{Fore.CYAN}Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Backup
    backup_path = backup_database()
    
    # Conectar
    print_header("ANÁLISIS DE OPORTUNIDADES")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        print_success("Conectado a la base de datos")
        
        # Obtener oportunidades sin nombre
        opportunities = get_opportunities_without_name(conn)
        
        if not opportunities:
            print_success("¡Todas las oportunidades ya tienen nombre!")
            conn.close()
            return
        
        print_warning(f"Encontradas {len(opportunities)} oportunidades sin nombre")
        
        print_info("\nOportunidades a actualizar:")
        for opp in opportunities[:10]:  # Mostrar primeras 10
            opp_id_short = opp[0][:12]
            account_name = opp[2]
            value = opp[3]
            print(f"  {Fore.YELLOW}{opp_id_short}... → {account_name} ({value}€)")
        
        if len(opportunities) > 10:
            print(f"  {Fore.BLUE}... y {len(opportunities) - 10} más")
        
        # Confirmar
        print(f"\n{Fore.YELLOW}Se asignarán nombres en el formato:")
        print(f"{Fore.CYAN}  [Nombre Cuenta] - Oportunidad")
        
        print(f"\n{Fore.YELLOW}Ejemplos:")
        for opp in opportunities[:3]:
            account_name = opp[2]
            new_name = f"{account_name} - Oportunidad"
            print(f"{Fore.GREEN}  {account_name} → {new_name}")
        
        print(f"\n{Fore.RED}{Style.BRIGHT}¿CONTINUAR? (s/n): ", end="")
        confirm = input().strip().lower()
        
        if confirm != 's':
            print_warning("Operación cancelada")
            conn.close()
            return
        
        # Actualizar
        print_header("ACTUALIZANDO NOMBRES")
        
        updated = 0
        errors = 0
        
        for opp in opportunities:
            opp_id = opp[0]
            account_name = opp[2]
            
            # Generar nombre
            new_name = f"{account_name} - Oportunidad"
            
            try:
                update_opportunity_name(conn, opp_id, new_name)
                updated += 1
                print(f"{Fore.GREEN}✅ {opp_id[:12]}... → {new_name}")
            except Exception as e:
                errors += 1
                print(f"{Fore.RED}❌ {opp_id[:12]}... → Error: {e}")
        
        # Commit
        conn.commit()
        print_success(f"\nCambios guardados en la base de datos")
        
        # Resumen
        print_header("RESUMEN")
        print(f"{Fore.GREEN}Actualizadas: {updated}")
        print(f"{Fore.RED}Errores: {errors}")
        print(f"{Fore.CYAN}Backup: {backup_path}")
        
        # Verificar
        print_header("VERIFICACIÓN")
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM opportunities 
            WHERE name IS NULL OR name = ''
        """)
        
        remaining = cursor.fetchone()[0]
        
        if remaining == 0:
            print_success("✅ Todas las oportunidades tienen nombre ahora")
        else:
            print_warning(f"⚠️  Quedan {remaining} oportunidades sin nombre")
        
        # Ver algunas actualizadas
        print_info("\nEjemplos de oportunidades actualizadas:")
        cursor.execute("""
            SELECT o.id, o.name, a.name 
            FROM opportunities o
            JOIN accounts a ON o.account_id = a.id
            WHERE o.name LIKE '% - Oportunidad'
            LIMIT 5
        """)
        
        examples = cursor.fetchall()
        for ex in examples:
            print(f"  {Fore.GREEN}{ex[0][:12]}... → {ex[1]}")
        
        conn.close()
        
        print_header("SIGUIENTE PASO")
        print(f"{Fore.CYAN}Ahora ejecuta:")
        print(f"{Fore.YELLOW}  1. START_CRM.bat  (reiniciar servidor)")
        print(f"{Fore.YELLOW}  2. TEST_TASKS.bat  (verificar que funciona)")
        
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
        print(f"\n{Fore.YELLOW}Si algo salió mal, puedes restaurar desde:")
        print(f"{Fore.CYAN}  {backup_path}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Operación cancelada por usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n{Fore.RED}Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
