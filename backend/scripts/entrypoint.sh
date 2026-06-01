#!/bin/bash
set -e
if [ -n "$POSTGRES_HOST" ]; then
  DB_PORT="${POSTGRES_PORT:-5432}"
  echo "[entrypoint] Waiting for PostgreSQL at $POSTGRES_HOST:$DB_PORT..."
  until pg_isready -h "$POSTGRES_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -q; do sleep 1; done
else
  echo "[entrypoint] POSTGRES_HOST not set; relying on Django DATABASE_URL connection."
fi
echo "[entrypoint] DB ready. Running migrations..."
python manage.py migrate --noinput
mkdir -p /app/staticfiles /app/media
chown -R appuser:appuser /app/staticfiles /app/media
python manage.py collectstatic --noinput --clear
chown -R appuser:appuser /app/staticfiles /app/media
APP_PORT="${PORT:-8000}"
echo "[entrypoint] Starting Daphne (HTTP + WebSocket) on port $APP_PORT..."
exec su -s /bin/bash appuser -c "exec daphne -b 0.0.0.0 -p $APP_PORT config.asgi:application"
