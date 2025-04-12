#!/bin/bash

# filepath: /home/markmur88/Documentos/GitHub/conf3/scripts/setup_postgresql.sh

# Variables
NOMBRE_BASE_DATOS="api_db"
NOMBRE_USUARIO="markmur88"
CONTRASENA_SEGURA="Ptf8454Jd55"

# 1. Instalación de PostgreSQL
# echo "Instalando PostgreSQL..."
# sudo apt update
# sudo apt install postgresql postgresql-contrib -y

# 2. Habilitar y arrancar el servicio
echo "Habilitando y arrancando el servicio PostgreSQL..."
sudo service postgresql start
# sudo service postgresql status

# 3. Reiniciar el servicio (opcional)
# echo "Reiniciando el servicio PostgreSQL..."
# sudo service postgresql restart

# 4. Crear base de datos (fuera de un bloque DO)
echo "Creando la base de datos si no existe..."
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = '${NOMBRE_BASE_DATOS}'" | grep -q 1 || sudo -u postgres psql -c "CREATE DATABASE ${NOMBRE_BASE_DATOS};"

# 5. Crear usuario y asignar privilegios
echo "Configurando PostgreSQL..."
sudo -u postgres psql <<EOF
-- Crear usuario si no existe
DO \$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${NOMBRE_USUARIO}') THEN
      CREATE USER ${NOMBRE_USUARIO} WITH PASSWORD '${CONTRASENA_SEGURA}';
   END IF;
END
\$\$;

-- Asignar privilegios
GRANT ALL PRIVILEGES ON DATABASE ${NOMBRE_BASE_DATOS} TO ${NOMBRE_USUARIO};
GRANT CONNECT ON DATABASE ${NOMBRE_BASE_DATOS} TO ${NOMBRE_USUARIO};
GRANT CREATE ON DATABASE ${NOMBRE_BASE_DATOS} TO ${NOMBRE_USUARIO};

GRANT USAGE, CREATE ON SCHEMA public TO ${NOMBRE_USUARIO};
GRANT ALL PRIVILEGES ON SCHEMA public TO ${NOMBRE_USUARIO};
ALTER USER ${NOMBRE_USUARIO} CREATEDB;
ALTER SCHEMA public OWNER TO ${NOMBRE_USUARIO};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO ${NOMBRE_USUARIO};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ${NOMBRE_USUARIO};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${NOMBRE_USUARIO};
EOF

sudo -u postgres psql -c "\dn+ public"

echo "Configuración completada."