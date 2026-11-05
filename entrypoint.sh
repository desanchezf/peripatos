#!/bin/sh
set -e

echo "Esperando a Postgres..."
until python -c "
import os, sys
import psycopg2
try:
    psycopg2.connect(
        dbname=os.environ.get('POSTGRES_DB', 'peripatos'),
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

echo "Ejecutando initsetup..."
until python ./manage.py initsetup; do
  echo "Retrying initsetup..."
  sleep 5
done

# Desarrollo local: runserver (autoreload)
# Producción: usar entrypoint.prod.sh / gunicorn
exec python manage.py runserver 0.0.0.0:8000
