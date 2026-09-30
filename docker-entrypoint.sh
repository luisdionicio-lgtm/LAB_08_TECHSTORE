#!/bin/sh
set -eu

stop_services() {
  kill "$PID1" "$PID2" "$PID3" 2>/dev/null || true
}

trap stop_services INT TERM EXIT

# Inicializa la base una sola vez antes de levantar los tres procesos.
BACKEND_ID=initializer python -c "import app" 

SKIP_DB_INIT=1 BACKEND_ID=backend-1 gunicorn --bind 0.0.0.0:8081 --workers 1 --access-logfile - app:app &
PID1=$!
SKIP_DB_INIT=1 BACKEND_ID=backend-2 gunicorn --bind 0.0.0.0:8082 --workers 1 --access-logfile - app:app &
PID2=$!
SKIP_DB_INIT=1 BACKEND_ID=backend-3 gunicorn --bind 0.0.0.0:8083 --workers 1 --access-logfile - app:app &
PID3=$!

nginx -g 'daemon off;'
