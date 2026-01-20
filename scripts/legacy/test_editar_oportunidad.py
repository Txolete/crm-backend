"""
Test opcional - Verificar endpoints necesarios para edición
"""
import requests

BASE_URL = "http://localhost:8000"
session = requests.Session()

print("="*70)
print("TEST OPCIONAL - Endpoints para edición")
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

# Get stages
print("\n2. GET /config/stages (para select de stages):")
response = session.get(f"{BASE_URL}/config/stages")
if response.status_code == 200:
    stages = response.json()
    print(f"   ✅ {len(stages)} stages disponibles")
    open_stages = [s for s in stages if s['outcome'] == 'open']
    print(f"   - Stages abiertos: {len(open_stages)}")
    for stage in open_stages[:3]:
        print(f"     • {stage['name']} ({stage['key']})")
else:
    print(f"   ❌ Error: {response.status_code}")

# Get users
print("\n3. GET /admin/users (para select de owner):")
response = session.get(f"{BASE_URL}/admin/users")
if response.status_code == 200:
    data = response.json()
    users = data.get('users', data)
    print(f"   ✅ {len(users)} usuarios disponibles")
    for user in users[:3]:
        print(f"     • {user['name']} ({user['email']})")
else:
    print(f"   ❌ Error: {response.status_code}")

# Get first opportunity
print("\n4. GET primera oportunidad:")
response = session.get(f"{BASE_URL}/opportunities")
if response.status_code == 200:
    data = response.json()
    opps = data.get('opportunities', [])
    if opps:
        opp_id = opps[0]['id']
        print(f"   ✅ Primera oportunidad: {opp_id[:8]}...")
        
        # Test update
        print("\n5. TEST PUT /opportunities/{id} (actualización):")
        update_data = {
            "name": "TEST - Oportunidad editada",
            "expected_value_eur": 12345.67
        }
        response = session.put(f"{BASE_URL}/opportunities/{opp_id}", json=update_data)
        
        if response.status_code == 200:
            print(f"   ✅ Actualización exitosa")
            updated = response.json()
            print(f"   - Nuevo nombre: {updated.get('name')}")
            print(f"   - Nuevo valor: €{updated.get('expected_value_eur')}")
            
            # Restore original (optional)
            print("\n6. RESTAURAR valor original:")
            restore_data = {
                "name": opps[0].get('name'),
                "expected_value_eur": opps[0].get('expected_value_eur')
            }
            response = session.put(f"{BASE_URL}/opportunities/{opp_id}", json=restore_data)
            if response.status_code == 200:
                print(f"   ✅ Valor restaurado")
            
        else:
            print(f"   ❌ Error: {response.status_code}")
            try:
                error = response.json()
                print(f"   Detalle: {error}")
            except:
                pass
    else:
        print(f"   ⚠️ No hay oportunidades")
else:
    print(f"   ❌ Error: {response.status_code}")

print("\n" + "="*70)
print("✅ Si todos los pasos tienen ✅, la edición funcionará perfectamente")
print("="*70)
