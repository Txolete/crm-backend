"""
DEBUGGER AUTOMÁTICO - ENDPOINTS DE TAREAS
==========================================

Este script prueba todos los endpoints de tareas y genera un diagnóstico completo.

Uso:
    python test_tasks_api.py

Requisitos:
    - Servidor CRM corriendo en localhost:8000
    - Usuario admin con password admin123
    - pip install requests colorama
"""

import requests
import json
from datetime import datetime, timedelta
from colorama import init, Fore, Style
import sys

# Inicializar colorama para colores en consola
init(autoreset=True)

# Configuración
BASE_URL = "http://localhost:8000"
LOGIN_EMAIL = "admin@example.com"
LOGIN_PASSWORD = "admin123456"

# Resultados
results = {
    "passed": [],
    "failed": [],
    "warnings": []
}


def print_header(text):
    """Imprimir encabezado"""
    print("\n" + "=" * 80)
    print(f"{Fore.CYAN}{Style.BRIGHT}{text}")
    print("=" * 80)


def print_test(name):
    """Imprimir nombre de test"""
    print(f"\n{Fore.YELLOW}🧪 TEST: {name}")


def print_success(message):
    """Imprimir éxito"""
    print(f"{Fore.GREEN}✅ {message}")
    results["passed"].append(message)


def print_error(message):
    """Imprimir error"""
    print(f"{Fore.RED}❌ {message}")
    results["failed"].append(message)


def print_warning(message):
    """Imprimir advertencia"""
    print(f"{Fore.YELLOW}⚠️  {message}")
    results["warnings"].append(message)


def print_info(message):
    """Imprimir información"""
    print(f"{Fore.BLUE}ℹ️  {message}")


def print_data(label, data, max_length=200):
    """Imprimir datos de respuesta"""
    data_str = json.dumps(data, indent=2)
    if len(data_str) > max_length:
        data_str = data_str[:max_length] + "..."
    print(f"{Fore.MAGENTA}{label}:")
    print(f"{Style.DIM}{data_str}")


def make_request(method, endpoint, json_data=None, cookies=None, expected_status=200):
    """Hacer request HTTP y validar"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, cookies=cookies)
        elif method == "POST":
            response = requests.post(url, json=json_data, cookies=cookies)
        elif method == "PUT":
            response = requests.put(url, json=json_data, cookies=cookies)
        elif method == "DELETE":
            response = requests.delete(url, cookies=cookies)
        
        print_info(f"{method} {endpoint} → Status {response.status_code}")
        
        if response.status_code != expected_status:
            print_error(f"Expected {expected_status}, got {response.status_code}")
            try:
                print_data("Response", response.json())
            except:
                print_data("Response Text", {"text": response.text})
            return None
        
        return response
    
    except requests.exceptions.ConnectionError:
        print_error(f"No se puede conectar a {BASE_URL}")
        print_info("¿Está el servidor corriendo? Ejecuta START_CRM.bat")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error en request: {e}")
        return None


def login():
    """Login y obtener cookie de sesión"""
    print_header("PASO 1: LOGIN")
    
    print_test("Login con admin")
    
    response = make_request(
        "POST",
        "/auth/login",
        json_data={
            "email": LOGIN_EMAIL,
            "password": LOGIN_PASSWORD
        }
    )
    
    if not response:
        print_error("Login falló")
        sys.exit(1)
    
    # Obtener cookie
    cookies = response.cookies
    
    if not cookies:
        print_error("No se obtuvo cookie de sesión")
        sys.exit(1)
    
    print_success("Login exitoso")
    print_info(f"Cookie obtenida: {cookies}")
    
    return cookies


def get_test_data(cookies):
    """Obtener IDs de prueba de la BD"""
    print_header("PASO 2: OBTENER DATOS DE PRUEBA")
    
    # Obtener una oportunidad
    print_test("Obtener oportunidad de prueba")
    response = make_request("GET", "/opportunities", cookies=cookies)
    
    if not response:
        print_error("No se pudieron obtener oportunidades")
        return None, None, None
    
    data = response.json()
    opportunities = data.get("opportunities", [])
    
    if not opportunities:
        print_error("No hay oportunidades en la BD")
        print_info("Crea al menos una oportunidad desde el dashboard")
        return None, None, None
    
    opportunity = opportunities[0]
    opportunity_id = opportunity["id"]
    account_id = opportunity["account_id"]
    
    print_success(f"Oportunidad encontrada: {opportunity_id}")
    print_info(f"Nombre: {opportunity.get('name', 'Sin nombre')}")
    print_info(f"Account ID: {account_id}")
    
    # Obtener account para verificar nombre
    print_test("Obtener cuenta de prueba")
    response = make_request("GET", f"/accounts/{account_id}", cookies=cookies)
    
    account_name = None
    if response:
        account = response.json()
        account_name = account.get("name", "Sin nombre")
        print_success(f"Cuenta encontrada: {account_name}")
    
    # Obtener usuario actual
    print_test("Obtener usuario actual")
    response = make_request("GET", "/auth/me", cookies=cookies)
    
    user_id = None
    if response:
        user = response.json()
        user_id = user["id"]
        print_success(f"Usuario: {user['name']} (ID: {user_id})")
    
    return opportunity_id, account_id, user_id


def test_list_tasks(cookies):
    """Test: Listar tareas"""
    print_header("PASO 3: LISTAR TAREAS")
    
    print_test("GET /tasks")
    response = make_request("GET", "/tasks", cookies=cookies)
    
    if not response:
        return
    
    data = response.json()
    tasks = data.get("tasks", [])
    total = data.get("total", 0)
    
    print_success(f"Listado obtenido: {total} tareas")
    
    if tasks:
        # Verificar primera tarea
        task = tasks[0]
        print_info("Verificando estructura de primera tarea:")
        
        fields_to_check = [
            "id", "title", "priority", "status", "due_date",
            "opportunity_id", "account_id", 
            "opportunity_name", "account_name", "assigned_to_name"
        ]
        
        for field in fields_to_check:
            value = task.get(field)
            if value is None:
                print_warning(f"  {field}: NULL")
            else:
                print_info(f"  {field}: {value}")
        
        # Verificar nombres
        if task.get("opportunity_name"):
            print_success("opportunity_name está presente")
        else:
            if task.get("opportunity_id"):
                print_error("opportunity_name es NULL pero opportunity_id existe")
        
        if task.get("account_name"):
            print_success("account_name está presente")
        else:
            if task.get("account_id"):
                print_error("account_name es NULL pero account_id existe")
        
        if task.get("assigned_to_name"):
            print_success("assigned_to_name está presente")
        else:
            if task.get("assigned_to_user_id"):
                print_error("assigned_to_name es NULL pero assigned_to_user_id existe")


def test_create_task_with_opportunity(cookies, opportunity_id, user_id):
    """Test: Crear tarea vinculada a oportunidad"""
    print_header("PASO 4: CREAR TAREA CON OPORTUNIDAD")
    
    print_test("POST /tasks (con opportunity_id)")
    
    task_data = {
        "opportunity_id": opportunity_id,
        "account_id": None,
        "title": f"Test: Llamar cliente - {datetime.now().strftime('%H:%M:%S')}",
        "description": "Tarea de prueba creada por debugger",
        "priority": "high",
        "due_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
        "assigned_to_user_id": user_id
    }
    
    print_data("Request Body", task_data)
    
    response = make_request(
        "POST",
        "/tasks",
        json_data=task_data,
        cookies=cookies,
        expected_status=201
    )
    
    if not response:
        return None
    
    task = response.json()
    task_id = task["id"]
    
    print_success(f"Tarea creada: {task_id}")
    print_data("Response", task, max_length=400)
    
    # Verificar campos
    if task.get("status") == "open":
        print_success("Status = open ✓")
    else:
        print_error(f"Status esperado 'open', recibido '{task.get('status')}'")
    
    if task.get("priority") == "high":
        print_success("Priority = high ✓")
    else:
        print_error(f"Priority esperado 'high', recibido '{task.get('priority')}'")
    
    return task_id


def test_create_task_with_account(cookies, account_id, user_id):
    """Test: Crear tarea vinculada a cuenta"""
    print_header("PASO 5: CREAR TAREA CON CUENTA")
    
    print_test("POST /tasks (con account_id)")
    
    task_data = {
        "opportunity_id": None,
        "account_id": account_id,
        "title": f"Test: Enviar catálogo - {datetime.now().strftime('%H:%M:%S')}",
        "description": "Tarea de prueba vinculada a cuenta",
        "priority": "medium",
        "due_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
        "assigned_to_user_id": user_id
    }
    
    print_data("Request Body", task_data)
    
    response = make_request(
        "POST",
        "/tasks",
        json_data=task_data,
        cookies=cookies,
        expected_status=201
    )
    
    if not response:
        return None
    
    task = response.json()
    task_id = task["id"]
    
    print_success(f"Tarea creada: {task_id}")
    print_data("Response", task, max_length=400)
    
    return task_id


def test_create_task_without_link(cookies, user_id):
    """Test: Intentar crear tarea sin vinculación (debe fallar)"""
    print_header("PASO 6: CREAR TAREA SIN VINCULACIÓN (DEBE FALLAR)")
    
    print_test("POST /tasks (sin opportunity_id ni account_id)")
    
    task_data = {
        "opportunity_id": None,
        "account_id": None,
        "title": "Tarea sin vinculación",
        "priority": "low"
    }
    
    print_data("Request Body", task_data)
    
    response = make_request(
        "POST",
        "/tasks",
        json_data=task_data,
        cookies=cookies,
        expected_status=400  # Esperamos error
    )
    
    if response:
        error = response.json()
        detail = error.get("detail", "")
        
        if "must be linked" in detail.lower():
            print_success("Validación correcta: rechaza tarea sin vinculación")
            print_info(f"Mensaje: {detail}")
        else:
            print_error(f"Mensaje de error inesperado: {detail}")


def test_get_task(cookies, task_id):
    """Test: Obtener una tarea específica"""
    print_header("PASO 7: OBTENER TAREA ESPECÍFICA")
    
    print_test(f"GET /tasks/{task_id}")
    
    response = make_request("GET", f"/tasks/{task_id}", cookies=cookies)
    
    if not response:
        return
    
    task = response.json()
    
    print_success("Tarea obtenida")
    print_data("Task Data", task, max_length=500)
    
    # Verificar campos con nombres
    print_info("\nVerificando campos de nombres:")
    
    name_fields = {
        "opportunity_name": task.get("opportunity_id"),
        "account_name": task.get("account_id"),
        "assigned_to_name": task.get("assigned_to_user_id")
    }
    
    for name_field, id_field in name_fields.items():
        value = task.get(name_field)
        
        if id_field and not value:
            print_error(f"{name_field} es NULL pero tiene ID asociado")
        elif value:
            print_success(f"{name_field} = {value}")
        else:
            print_info(f"{name_field} = NULL (sin ID asociado)")


def test_complete_task(cookies, task_id):
    """Test: Completar tarea"""
    print_header("PASO 8: COMPLETAR TAREA")
    
    print_test(f"POST /tasks/{task_id}/complete")
    
    response = make_request(
        "POST",
        f"/tasks/{task_id}/complete",
        cookies=cookies
    )
    
    if not response:
        return
    
    task = response.json()
    
    if task.get("status") == "completed":
        print_success("Status = completed ✓")
    else:
        print_error(f"Status esperado 'completed', recibido '{task.get('status')}'")
    
    if task.get("completed_at"):
        print_success(f"completed_at = {task.get('completed_at')} ✓")
    else:
        print_error("completed_at es NULL")
    
    if task.get("completed_by_user_id"):
        print_success(f"completed_by_user_id = {task.get('completed_by_user_id')} ✓")
    else:
        print_error("completed_by_user_id es NULL")


def test_get_opportunity_tasks(cookies, opportunity_id):
    """Test: Obtener tareas de oportunidad"""
    print_header("PASO 9: TAREAS DE OPORTUNIDAD")
    
    print_test(f"GET /tasks/opportunity/{opportunity_id}")
    
    response = make_request(
        "GET",
        f"/tasks/opportunity/{opportunity_id}",
        cookies=cookies
    )
    
    if not response:
        return
    
    data = response.json()
    tasks = data.get("tasks", [])
    total = data.get("total", 0)
    
    print_success(f"Tareas obtenidas: {total}")
    
    if tasks:
        print_info("Primera tarea:")
        print_data("Task", tasks[0], max_length=300)


def test_get_account_tasks(cookies, account_id):
    """Test: Obtener tareas de cuenta"""
    print_header("PASO 10: TAREAS DE CUENTA")
    
    print_test(f"GET /tasks/account/{account_id}")
    
    response = make_request(
        "GET",
        f"/tasks/account/{account_id}",
        cookies=cookies
    )
    
    if not response:
        return
    
    data = response.json()
    tasks = data.get("tasks", [])
    total = data.get("total", 0)
    
    print_success(f"Tareas obtenidas: {total}")
    print_info("Incluye tareas directas de cuenta + tareas de oportunidades de la cuenta")
    
    if tasks:
        print_info("Primera tarea:")
        print_data("Task", tasks[0], max_length=300)


def test_filters(cookies):
    """Test: Filtros de listado"""
    print_header("PASO 11: FILTROS")
    
    # Filtro por estado
    print_test("GET /tasks?status=open")
    response = make_request("GET", "/tasks?status=open", cookies=cookies)
    if response:
        data = response.json()
        print_success(f"Tareas abiertas: {data.get('total', 0)}")
    
    # Filtro por prioridad
    print_test("GET /tasks?priority=high")
    response = make_request("GET", "/tasks?priority=high", cookies=cookies)
    if response:
        data = response.json()
        print_success(f"Tareas alta prioridad: {data.get('total', 0)}")
    
    # Filtro atrasadas
    print_test("GET /tasks?overdue=true")
    response = make_request("GET", "/tasks?overdue=true", cookies=cookies)
    if response:
        data = response.json()
        print_success(f"Tareas atrasadas: {data.get('total', 0)}")


def print_summary():
    """Imprimir resumen final"""
    print_header("RESUMEN FINAL")
    
    total_tests = len(results["passed"]) + len(results["failed"])
    
    print(f"\n{Fore.CYAN}📊 RESULTADOS:")
    print(f"{Fore.GREEN}✅ Pasados: {len(results['passed'])}")
    print(f"{Fore.RED}❌ Fallidos: {len(results['failed'])}")
    print(f"{Fore.YELLOW}⚠️  Advertencias: {len(results['warnings'])}")
    
    if results["failed"]:
        print(f"\n{Fore.RED}{Style.BRIGHT}ERRORES ENCONTRADOS:")
        for error in results["failed"]:
            print(f"{Fore.RED}  ❌ {error}")
    
    if results["warnings"]:
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}ADVERTENCIAS:")
        for warning in results["warnings"]:
            print(f"{Fore.YELLOW}  ⚠️  {warning}")
    
    # Diagnóstico
    print(f"\n{Fore.CYAN}{Style.BRIGHT}🔍 DIAGNÓSTICO:")
    
    if "account_name es NULL pero account_id existe" in str(results["failed"]):
        print(f"{Fore.RED}  🐛 PROBLEMA DETECTADO: account_name no se está cargando")
        print(f"{Fore.YELLOW}     Causa probable: Error en la query de nombres en tasks.py")
        print(f"{Fore.YELLOW}     Solución: Verificar el código que carga account_name")
    
    if "opportunity_name es NULL pero opportunity_id existe" in str(results["failed"]):
        print(f"{Fore.RED}  🐛 PROBLEMA DETECTADO: opportunity_name no se está cargando")
        print(f"{Fore.YELLOW}     Causa probable: Error en la query de nombres en tasks.py")
        print(f"{Fore.YELLOW}     Solución: Verificar el código que carga opportunity_name")
    
    if len(results["failed"]) == 0:
        print(f"{Fore.GREEN}  ✅ TODO FUNCIONA CORRECTAMENTE")
    
    print("\n" + "=" * 80)


def main():
    """Función principal"""
    print_header("🔧 DEBUGGER AUTOMÁTICO - ENDPOINTS DE TAREAS")
    print(f"{Fore.CYAN}Base URL: {BASE_URL}")
    print(f"{Fore.CYAN}Usuario: {LOGIN_EMAIL}")
    print(f"{Fore.CYAN}Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Login
    cookies = login()
    
    # Obtener datos de prueba
    opportunity_id, account_id, user_id = get_test_data(cookies)
    
    if not all([opportunity_id, account_id, user_id]):
        print_error("No se pudieron obtener datos de prueba")
        print_info("Asegúrate de tener al menos una oportunidad creada")
        sys.exit(1)
    
    # Tests
    test_list_tasks(cookies)
    task_id_opp = test_create_task_with_opportunity(cookies, opportunity_id, user_id)
    task_id_acc = test_create_task_with_account(cookies, account_id, user_id)
    test_create_task_without_link(cookies, user_id)
    
    if task_id_opp:
        test_get_task(cookies, task_id_opp)
        test_complete_task(cookies, task_id_opp)
    
    test_get_opportunity_tasks(cookies, opportunity_id)
    test_get_account_tasks(cookies, account_id)
    test_filters(cookies)
    
    # Resumen
    print_summary()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Test interrumpido por usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n{Fore.RED}Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
