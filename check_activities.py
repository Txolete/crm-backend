import psycopg2

conn = psycopg2.connect('postgresql://postgres:TCnUhilkBgyZSRQuMduxCEgVMCVVMexJ@hopper.proxy.rlwy.net:58218/railway')
cur = conn.cursor()

# Buscar la oportunidad
cur.execute("""
    SELECT o.id, o.name, a.name as account_name
    FROM opportunities o
    JOIN accounts a ON o.account_id = a.id
    WHERE o.name ILIKE '%sustaining air%'
    OR a.name ILIKE '%sustaining air%'
""")
opps = cur.fetchall()
print("Oportunidades encontradas:")
for o in opps:
    print(f"  ID: {o[0]} | Opp: {o[1]} | Cuenta: {o[2]}")

if opps:
    opp_id = opps[0][0]
    print(f"\nActividades para oportunidad {opp_id}:")
    cur.execute("""
        SELECT occurred_at, type, summary
        FROM activities
        WHERE opportunity_id = %s
        ORDER BY occurred_at ASC
    """, (opp_id,))
    activities = cur.fetchall()
    for act in activities:
        line = f"  [{act[0].strftime('%Y-%m-%d')}] ({act[1]}): {act[2]}"
        print(line.encode('cp1252', errors='replace').decode('cp1252'))

cur.close()
conn.close()
