#!/bin/bash

MYSQL_HOST=${MYSQL_HOST:-mysql}
MYSQL_PORT=${MYSQL_PORT:-3306}
MYSQL_USER=${MYSQL_USER:-root}
MYSQL_PASSWORD=${MYSQL_PASSWORD:-root}
MYSQL_DB=${MYSQL_DB:-bankingapp}

echo "Esperando a que MySQL esté disponible en $MYSQL_HOST:$MYSQL_PORT..."

# Comprobar la conexión al servidor MySQL
while ! mysqladmin ping -h"$MYSQL_HOST" -P"$MYSQL_PORT" --silent; do
  echo "MySQL no está listo aún. Esperando..."
  sleep 2
done

echo "MySQL está listo. Ejecutando la aplicación."

# Ejecutar el comando original
exec "$@"
