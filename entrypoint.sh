#!/bin/sh

set -e

echo "Aguardando PostgreSQL..."

while ! nc -z db 5432; do
  sleep 1
done

echo "PostgreSQL disponível."

echo "Aplicando migrações..."
python manage.py migrate --noinput

echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "Iniciando Gunicorn..."
exec gunicorn catalisa.wsgi:application --bind 0.0.0.0:8000 --workers 3