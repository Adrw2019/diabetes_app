#!/usr/bin/env bash
set -euo pipefail

DOTENV_FILE=".env"

if [[ ! -f $DOTENV_FILE ]]; then
  echo "❌ $DOTENV_FILE no existe. Crea uno basado en .env.example antes de continuar." >&2
  exit 1
fi

echo "🔐 Cargando variables desde $DOTENV_FILE"
set -a
# shellcheck disable=SC1091
source "$DOTENV_FILE"
set +a

echo "🚀 Ejecutando migraciones y collectstatic"
python manage.py migrate
python manage.py collectstatic --noinput

echo "✅ Entorno listo."
