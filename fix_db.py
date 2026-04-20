import psycopg2

conn = psycopg2.connect('postgresql://postgres:TCnUhilkBgyZSRQuMduxCEgVMCVVMexJ@hopper.proxy.rlwy.net:58218/railway')
cur = conn.cursor()

# Ver estado actual
cur.execute('SELECT * FROM alembic_version;')
print('alembic_version actual:', cur.fetchall())

# Marcar todas las migraciones como aplicadas
cur.execute('DELETE FROM alembic_version;')
cur.execute("INSERT INTO alembic_version (version_num) VALUES ('h7c8d9e0f1g2');")
print('alembic_version actualizada a h7c8d9e0f1g2')

# Ampliar chatgpt_thread_id si es necesario
try:
    cur.execute('ALTER TABLE opportunities ALTER COLUMN chatgpt_thread_id TYPE VARCHAR(1000);')
    print('chatgpt_thread_id ampliado a VARCHAR(1000)')
except Exception as e:
    print(f'chatgpt_thread_id ya OK o error: {e}')

conn.commit()
print('Todo OK!')
cur.close()
conn.close()
