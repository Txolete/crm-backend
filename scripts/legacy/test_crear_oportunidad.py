"""
DIAGNÓSTICO - Crear Oportunidad
Prueba el flujo completo de creación de oportunidad
"""
import requests
import json

BASE_URL = "http://localhost:8000"
session = requests.Session()

print("="*70)
print("DIAGNÓSTICO - CREAR OPORTUNIDAD")
print("="*70)

# Login
print("\n1. LOGIN:")
login_data = {
    "email": "admin@example.com",
    "password": "admin123456"
}
response = session.post(f"{BASE_URL}/auth/login", json=login_data)
if response.status_code == 200:
    print("   ✅ Login exitoso")
else:
    print(f"   ❌ Login falló: {response.status_code}")
    exit(1)

# Get accounts
print("\n2. GET ACCOUNTS:")
response = session.get(f"{BASE_URL}/accounts?status=active")
if response.status_code == 200:
    data = response.json()
    accounts = data.get('accounts', [])
    print(f"   ✅ {len(accounts)} cuentas disponibles")
    if accounts:
        account_id = accounts[0]['id']
        account_name = accounts[0]['name']
        print(f"   Primera cuenta: {account_name} (ID: {account_id[:8]})")
    else:
        print(f"   ❌ No hay cuentas")
        exit(1)
else:
    print(f"   ❌ Error: {response.status_code}")
    exit(1)

# Get stages
print("\n3. GET STAGES:")
response = session.get(f"{BASE_URL}/config/stages")
if response.status_code == 200:
    stages = response.json()
    open_stages = [s for s in stages if s['outcome'] == 'open']
    print(f"   ✅ {len(stages)} stages totales")
    print(f"   ✅ {len(open_stages)} stages abiertos")
    if open_stages:
        stage_id = open_stages[0]['id']
        stage_name = open_stages[0]['name']
        print(f"   Primer stage abierto: {stage_name} (ID: {stage_id[:8]})")
    else:
        print(f"   ❌ No hay stages abiertos")
        exit(1)
else:
    print(f"   ❌ Error: {response.status_code}")
    exit(1)

# Get current user
print("\n4. GET CURRENT USER:")
response = session.get(f"{BASE_URL}/auth/me")
if response.status_code == 200:
    user = response.json()
    user_id = user['id']
    print(f"   ✅ Usuario: {user['email']} (ID: {user_id[:8]})")
else:
    print(f"   ❌ Error: {response.status_code}")
    user_id = None

# Create opportunity
print("\n5. CREATE OPPORTUNITY:")
opportunity_data = {
    "account_id": account_id,
    "name": "Test - Oportunidad de Prueba",
    "stage_id": stage_id,
    "expected_value_eur": 5000.0,
    "forecast_close_month": "2026-02",
    "owner_user_id": user_id
}

print(f"   Datos a enviar:")
print(f"   - Cuenta: {account_name}")
print(f"   - Stage: {stage_name}")
print(f"   - Valor: €5,000")
print(f"   - Owner: {user_id[:8] if user_id else 'null'}")

response = session.post(
    f"{BASE_URL}/opportunities",
    headers={'Content-Type': 'application/json'},
    json=opportunity_data
)

print(f"\n   Response status: {response.status_code}")

if response.status_code == 201:
    created_opp = response.json()
    print(f"   ✅ Oportunidad creada exitosamente!")
    print(f"   ID: {created_opp['id'][:8]}")
    print(f"   Nombre: {created_opp['name']}")
    print(f"   Valor: €{created_opp['expected_value_eur']}")
    
    # Verify it appears in Kanban
    print("\n6. VERIFICAR EN KANBAN:")
    response = session.get(f"{BASE_URL}/kanban?include_closed=false")
    if response.status_code == 200:
        data = response.json()
        total_opps = sum(len(col['opportunities']) for col in data['columns'])
        print(f"   ✅ Kanban cargado: {total_opps} oportunidades totales")
        
        # Find our opportunity
        found = False
        for col in data['columns']:
            for opp in col['opportunities']:
                if opp['opportunity_id'] == created_opp['id']:
                    print(f"   ✅ Oportunidad encontrada en columna: {col['stage_name']}")
                    found = True
                    break
            if found:
                break
        
        if not found:
            print(f"   ⚠️ Oportunidad NO aparece en Kanban")
    else:
        print(f"   ❌ Error cargando Kanban: {response.status_code}")
        
elif response.status_code == 422:
    print(f"   ❌ Error de validación (422)")
    error_detail = response.json()
    print(f"   Detalle: {json.dumps(error_detail, indent=2)}")
else:
    print(f"   ❌ Error {response.status_code}")
    try:
        error_detail = response.json()
        print(f"   Detalle: {json.dumps(error_detail, indent=2)}")
    except:
        print(f"   Body: {response.text}")

print("\n" + "="*70)
print("RESULTADO:")
if response.status_code == 201:
    print("✅ La creación de oportunidades FUNCIONA correctamente")
    print("   El problema debe estar en el frontend (JavaScript)")
else:
    print("❌ La creación de oportunidades FALLA en el backend")
    print("   Hay que arreglar el endpoint primero")
print("="*70)
