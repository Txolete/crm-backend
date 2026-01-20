"""
PASO 1: Verificar estado de la base de datos
"""
import sqlite3

db_path = 'crm.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("="*70)
print("VERIFICACIÓN DE BASE DE DATOS")
print("="*70)

# 1. Verificar stages
print("\n1. STAGES:")
cursor.execute("SELECT id, key, name, outcome FROM cfg_stages ORDER BY sort_order")
stages = cursor.fetchall()
print(f"   Total stages: {len(stages)}")
for stage in stages:
    print(f"   - {stage[1]}: {stage[2]} (outcome: {stage[3]})")

# 2. Verificar accounts
print("\n2. ACCOUNTS:")
cursor.execute("SELECT id, name, status FROM accounts")
accounts = cursor.fetchall()
print(f"   Total accounts: {len(accounts)}")
for acc in accounts[:5]:
    print(f"   - {acc[1]} (status: {acc[2]})")
if len(accounts) > 5:
    print(f"   ... y {len(accounts)-5} más")

# 3. Verificar opportunities
print("\n3. OPPORTUNITIES:")
cursor.execute("""
    SELECT o.id, o.name, o.stage_id, o.status, o.expected_value_eur, a.name
    FROM opportunities o
    LEFT JOIN accounts a ON o.account_id = a.id
""")
opps = cursor.fetchall()
print(f"   Total opportunities: {len(opps)}")
print(f"\n   Primeras 5 oportunidades:")
for opp in opps[:5]:
    print(f"   - [{opp[3]}] {opp[1] or 'Sin nombre'} @ {opp[5]} (stage: {opp[2][:8]}, valor: {opp[4]}€)")

# 4. Verificar distribution por stage
print("\n4. DISTRIBUCIÓN POR STAGE:")
cursor.execute("""
    SELECT s.name, COUNT(o.id) as count
    FROM cfg_stages s
    LEFT JOIN opportunities o ON o.stage_id = s.id AND o.status = 'active'
    GROUP BY s.id, s.name
    ORDER BY s.sort_order
""")
dist = cursor.fetchall()
for stage_name, count in dist:
    print(f"   - {stage_name}: {count} oportunidades")

# 5. Verificar si hay stage_ids inválidos
print("\n5. VERIFICAR STAGE_IDS INVÁLIDOS:")
cursor.execute("""
    SELECT o.id, o.name, o.stage_id
    FROM opportunities o
    WHERE o.status = 'active'
    AND o.stage_id NOT IN (SELECT id FROM cfg_stages)
""")
invalid = cursor.fetchall()
if invalid:
    print(f"   ❌ {len(invalid)} oportunidades con stage_id INVÁLIDO:")
    for opp in invalid[:3]:
        print(f"   - {opp[1] or 'Sin nombre'}: stage_id={opp[2]}")
else:
    print(f"   ✅ Todas las oportunidades tienen stage_id válido")

# 6. Verificar oportunidades activas
print("\n6. OPORTUNIDADES POR STATUS:")
cursor.execute("""
    SELECT status, COUNT(*) as count
    FROM opportunities
    GROUP BY status
""")
status_dist = cursor.fetchall()
for status, count in status_dist:
    print(f"   - {status}: {count}")

conn.close()

print("\n" + "="*70)
print("RESUMEN:")
print(f"✅ Stages: {len(stages)}")
print(f"✅ Accounts: {len(accounts)}")
print(f"✅ Opportunities: {len(opps)}")
if invalid:
    print(f"❌ Oportunidades con stage_id inválido: {len(invalid)}")
else:
    print(f"✅ Todas las oportunidades tienen stage_id válido")
print("="*70)
