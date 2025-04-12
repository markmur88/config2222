#!/bin/bash

# filepath: /home/markmur88/Documentos/GitHub/conf3/scripts/setup_postgresql.sh

# Variables
NOMBRE_BASE_DATOS="api_db"
NOMBRE_USUARIO="markmur88"
CONTRASENA_SEGURA="Ptf8454Jd55"

# 1. Instalación de PostgreSQL
echo "Instalando PostgreSQL..."
sudo apt update
sudo apt install postgresql postgresql-contrib -y

# 2. Habilitar y arrancar el servicio
echo "Habilitando y arrancando el servicio PostgreSQL..."
sudo service postgresql start
sudo service postgresql status

# 3. Reiniciar el servicio (opcional)
echo "Reiniciando el servicio PostgreSQL..."
sudo service postgresql restart

# 4. Acceso al cliente psql como usuario postgres y configuración
echo "Configurando PostgreSQL..."
sudo -u postgres psql <<EOF
-- Crear base de datos
DO \$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '${NOMBRE_BASE_DATOS}') THEN
      CREATE DATABASE ${NOMBRE_BASE_DATOS};
   END IF;
END
\$\$;

-- Crear usuario
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
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO ${NOMBRE_USUARIO};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ${NOMBRE_USUARIO};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${NOMBRE_USUARIO};
EOF

echo "Configuración completada."