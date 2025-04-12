#!/bin/bash

# Crear y activar un entorno virtual
python3 -m venv env
source env/bin/activate

# Instalar Django y otros paquetes necesarios
pip install django gunicorn

# Crear un nuevo proyecto Django
django-admin startproject myproject

# Moverse al directorio del proyecto
cd myproject

# Crear una nueva aplicación Django
python manage.py startapp main

# Crear un archivo requirements.txt
echo "django" > requirements.txt
echo "gunicorn" >> requirements.txt

# Crear un archivo Procfile para Render.com
echo "web: gunicorn myproject.wsgi" > Procfile

# Crear un archivo runtime.txt para especificar la versión de Python
echo "python-3.8.12" > runtime.txt

# Realizar migraciones iniciales
python manage.py migrate

# Crear un superusuario
python manage.py createsuperuser

# Iniciar el servidor de desarrollo
python manage.py runserver
