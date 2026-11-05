#!/bin/sh
set -e

echo "Esperando a Postgres..."
until python -c "
import os, sys
import psycopg2
try:
    psycopg2.connect(
        dbname=os.environ.get('POSTGRES_DB', 'postgres'),
        user=os.environ.get('POSTGRES_USER', 'postgres'),
        password=os.environ.get('POSTGRES_PASSWORD', 'postgres'),
        host=os.environ.get('POSTGRES_HOST', 'postgres'),
        port=os.environ.get('POSTGRES_PORT', '5432'),
    )
except Exception as e:
    print(e)
    sys.exit(1)
"; do
  echo "Postgres no listo; reintentando en 2s..."
  sleep 2
done

python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py initsetup || true

# Varios workers para usuarios concurrentes
# Override con GUNICORN_WORKERS / GUNICORN_THREADS en .env
WORKERS="${GUNICORN_WORKERS:-4}"
THREADS="${GUNICORN_THREADS:-2}"
TIMEOUT="${GUNICORN_TIMEOUT:-60}"

exec gunicorn project.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "$WORKERS" \
  --threads "$THREADS" \
  --timeout "$TIMEOUT" \
  --access-logfile - \
  --error-logfile - \
  --worker-tmp-dir /dev/shm
