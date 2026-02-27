import psycopg2
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

conn = psycopg2.connect(
    dbname=os.environ.get('DB_NAME'),
    user=os.environ.get('DB_USER'),
    password=os.environ.get('DB_PASSWORD'),
    host=os.environ.get('DB_HOST'),
    port=os.environ.get('DB_PORT'),
    sslmode='require'
)
conn.autocommit = True
cur = conn.cursor()

# 1. Hacer nullable el campo 'name' de django_content_type (Django 4+ ya no lo usa)
try:
    cur.execute("ALTER TABLE django_content_type ALTER COLUMN name DROP NOT NULL;")
    print("[OK] django_content_type.name -> nullable")
except Exception as e:
    print(f"[INFO] django_content_type.name: {e}")

# 2. Hacer nullable el campo 'updated_at' de activities y subtasks (por si acaso)
for table in ['activities', 'subtasks']:
    try:
        cur.execute(f"ALTER TABLE {table} ALTER COLUMN updated_at DROP NOT NULL;")
        print(f"[OK] {table}.updated_at -> nullable")
    except Exception as e:
        print(f"[INFO] {table}.updated_at: {e}")

# 3. Asegurar que last_login en auth_user sea nullable
try:
    cur.execute("ALTER TABLE auth_user ALTER COLUMN last_login DROP NOT NULL;")
    print("[OK] auth_user.last_login -> nullable")
except Exception as e:
    print(f"[INFO] auth_user.last_login: {e}")

conn.close()
print("\nTodas las correcciones aplicadas correctamente.")
