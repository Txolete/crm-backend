"""
PASO 3: Debug profundo del Kanban
Compara query SQL directa vs endpoint
"""
import sqlite3
import requests

print("="*70)
print("DEBUG PROFUNDO - KANBAN")
print("="*70)

# 1. Query SQL directa - simula lo que hace el endpoint
print("\n1. QUERY SQL DIRECTA:")
conn = sqlite3.connect('crm.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT 
        o.id,
        o.name,
        o.stage_id,
        o.status,
        o.expected_value_eur,
        s.name as stage_name,
        s.key as stage_key,
        a.name as account_name
    FROM opportunities o
    JOIN cfg_stages s ON o.stage_id = s.id
    JOIN accounts a ON o.account_id = a.id
    WHERE o.status = 'active'
    ORDER BY s.sort_order, o.expected_value_eur DESC
""")

rows = cursor.fetchall()
print(f"   Total oportunidades activas: {len(rows)}")

# Agrupar por stage
from collections import defaultdict
by_stage = defaultdict(list)
for row in rows:
    stage_key = row[6]
    by_stage[stage_key].append({
        'id': row[0],
        'name': row[1],
        'stage_id': row[2],
        'status': row[3],
        'value': row[4],
        'account': row[7]
    })

print(f"\n   Distribución por stage:")
for stage_key, opps in by_stage.items():
    print(f"      - {stage_key}: {len(opps)} opps")
    if opps:
        print(f"        Ejemplo: {opps[0]['name'] or 'Sin nombre'} @ {opps[0]['account']}")

conn.close()

# 2. Endpoint /kanban
print("\n2. ENDPOINT /kanban:")
session = requests.Session()

# Login
login_data = {"email": "admin@example.com", "password": "admin123456"}
response = session.post("http://localhost:8000/auth/login", json=login_data)

if response.status_code != 200:
    print(f"   ❌ Login falló")
    exit(1)

# Get kanban
response = session.get("http://localhost:8000/kanban?include_closed=true")

if response.status_code != 200:
    print(f"   ❌ Kanban falló: {response.status_code}")
    print(f"   {response.text}")
else:
    data = response.json()
    print(f"   ✅ Status 200")
    
    columns = data.get('columns', [])
    print(f"\n   Distribución por columna:")
    
    for col in columns:
        stage_key = col.get('stage_key', '?')
        opps = col.get('opportunities', [])
        print(f"      - {stage_key}: {len(opps)} opps")
        
        if opps:
            print(f"        Ejemplo: {opps[0].get('opportunity_name') or 'Sin nombre'} @ {opps[0].get('account_name')}")

# 3. Comparación
print("\n3. COMPARACIÓN:")
print("   SQL directa encontró:", len(rows), "oportunidades")
print("   Endpoint /kanban devolvió:", sum(len(col.get('opportunities', [])) for col in columns), "oportunidades")

if len(rows) > 0 and sum(len(col.get('opportunities', [])) for col in columns) == 0:
    print("\n   ❌ PROBLEMA IDENTIFICADO:")
    print("   La base de datos tiene oportunidades PERO el endpoint no las devuelve")
    print("   Esto significa que hay un BUG en el código de kanban.py")
    print("\n   Posibles causas:")
    print("   1. El filtrado post-query está eliminando todas las oportunidades")
    print("   2. El mapeo de accounts_map está fallando")
    print("   3. Hay un problema con los stage_ids")
    
    # Verificar stage_ids
    print("\n4. VERIFICAR STAGE_IDS:")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT stage_id FROM opportunities WHERE status = 'active'")
    opp_stages = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT id FROM cfg_stages")
    valid_stages = [row[0] for row in cursor.fetchall()]
    
    print(f"   Stage_ids en opportunities: {len(opp_stages)}")
    print(f"   Stage_ids válidos en cfg_stages: {len(valid_stages)}")
    
    invalid = [s for s in opp_stages if s not in valid_stages]
    if invalid:
        print(f"\n   ❌ Hay {len(invalid)} stage_ids INVÁLIDOS en opportunities:")
        for s in invalid:
            print(f"      - {s}")
    else:
        print(f"   ✅ Todos los stage_ids son válidos")
    
elif len(rows) > 0 and sum(len(col.get('opportunities', [])) for col in columns) > 0:
    print("\n   ✅ El endpoint funciona correctamente")
else:
    print("\n   ⚠️ No hay oportunidades en la base de datos")

print("\n" + "="*70)
