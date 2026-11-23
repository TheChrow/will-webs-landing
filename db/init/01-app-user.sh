#!/bin/bash
# Se ejecuta UNA sola vez, al crear el volumen de MySQL.
# Crea el usuario de la aplicación con mínimo privilegio (solo DML).
# El usuario de migraciones (MYSQL_USER) lo crea la imagen oficial con ALL sobre MYSQL_DATABASE.
set -eo pipefail

if [ -n "${APP_DB_PASSWORD_FILE:-}" ] && [ -f "${APP_DB_PASSWORD_FILE}" ]; then
  APP_DB_PASSWORD="$(cat "${APP_DB_PASSWORD_FILE}")"
fi

: "${APP_DB_USER:?APP_DB_USER es obligatorio}"
: "${APP_DB_PASSWORD:?APP_DB_PASSWORD (o APP_DB_PASSWORD_FILE) es obligatorio}"
: "${MYSQL_DATABASE:?MYSQL_DATABASE es obligatorio}"

# Escapar comillas simples para el literal SQL.
pw_escaped="${APP_DB_PASSWORD//\'/\'\'}"

mysql --protocol=socket -uroot -p"${MYSQL_ROOT_PASSWORD}" <<SQL
CREATE USER IF NOT EXISTS '${APP_DB_USER}'@'%' IDENTIFIED BY '${pw_escaped}';
GRANT SELECT, INSERT, UPDATE, DELETE ON \`${MYSQL_DATABASE}\`.* TO '${APP_DB_USER}'@'%';
FLUSH PRIVILEGES;
SQL

echo "[init] usuario de aplicación '${APP_DB_USER}' creado con privilegios DML sobre '${MYSQL_DATABASE}'"

# Base de datos para tests de integración (solo desarrollo/CI).
if [ "${CREATE_TEST_DB:-0}" = "1" ]; then
  mysql --protocol=socket -uroot -p"${MYSQL_ROOT_PASSWORD}" <<SQL
CREATE DATABASE IF NOT EXISTS \`${MYSQL_DATABASE}_test\` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
GRANT ALL PRIVILEGES ON \`${MYSQL_DATABASE}_test\`.* TO '${MYSQL_USER}'@'%';
FLUSH PRIVILEGES;
SQL
  echo "[init] base de datos de tests '${MYSQL_DATABASE}_test' creada"
fi
