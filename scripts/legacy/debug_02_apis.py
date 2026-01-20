"""
PASO 2: Verificar APIs - Llamadas reales
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Necesitamos login primero para obtener cookie
session = requests.Session()

print("="*70)
print("VERIFICACIÓN DE APIs")
print("="*70)

# Login
print("\n1. LOGIN:")
login_data = {
    "email": "admin@example.com",
    "password": "admin123456"
}
try:
    response = session.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        print("   ✅ Login exitoso")
    else:
        print(f"   ❌ Login falló: {response.status_code}")
        print(f"   {response.text}")
        exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Test stages
print("\n2. GET /config/stages:")
try:
    response = session.get(f"{BASE_URL}/config/stages")
    if response.status_code == 200:
        stages = response.json()
        print(f"   ✅ Status 200 - {len(stages)} stages")
        for stage in stages:
            print(f"      - {stage['key']}: {stage['name']} (prob: {stage.get('probability', 0)*100:.0f}%)")
    else:
        print(f"   ❌ Status {response.status_code}")
        print(f"   {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test opportunities
print("\n3. GET /opportunities:")
try:
    response = session.get(f"{BASE_URL}/opportunities?status=active&limit=100")
    if response.status_code == 200:
        data = response.json()
        opps = data.get('opportunities', [])
        print(f"   ✅ Status 200 - {len(opps)} opportunities")
        if len(opps) > 0:
            print(f"\n   Primeras 3 oportunidades:")
            for opp in opps[:3]:
                print(f"      - {opp.get('name', 'Sin nombre')} @ {opp.get('account_name', '?')}")
                print(f"        stage_id: {opp['stage_id'][:8]}, status: {opp['status']}, valor: {opp['expected_value_eur']}€")
    else:
        print(f"   ❌ Status {response.status_code}")
        print(f"   {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test kanban - CRITICAL
print("\n4. GET /kanban:")
try:
    response = session.get(f"{BASE_URL}/kanban?include_closed=true")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Status 200")
        print(f"   Stages: {len(data.get('stages', []))}")
        print(f"   Columns: {len(data.get('columns', []))}")
        
        total_opps = 0
        for col in data.get('columns', []):
            opps_in_col = len(col.get('opportunities', []))
            total_opps += opps_in_col
            print(f"      - {col.get('stage_name', col.get('stage_key', '?'))}: {opps_in_col} opps")
        
        print(f"\n   Total oportunidades en Kanban: {total_opps}")
        
        if total_opps == 0:
            print(f"\n   ⚠️ KANBAN VACÍO - Esto es el problema")
            print(f"   Verificando estructura de respuesta...")
            print(f"   Columnas devueltas: {[col.get('stage_key') for col in data.get('columns', [])]}")
        else:
            print(f"\n   ✅ Kanban tiene oportunidades")
            
    else:
        print(f"   ❌ Status {response.status_code}")
        print(f"   {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*70)
print("SIGUIENTE PASO:")
print("Si GET /kanban está vacío pero GET /opportunities tiene datos,")
print("el problema está en la lógica de filtrado del endpoint /kanban")
print("="*70)
