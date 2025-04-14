# Swift App

## Descripción
swiftapi4 es un proyecto diseñado para proporcionar una API rápida y eficiente para [descripción breve del propósito del proyecto].

## Instalación

1. Crea y activa un entorno virtual, instala las dependencias y realiza las migraciones:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py collectstatic
   python -m pip install gunicorn
   gunicorn config.wsgi
2. Recopila los archivos estáticos:
   ```bash
   python manage.py collectstatic
3. Inicia el servidor de desarrollo:
   ```bash
   python manage.py runserver
4. Comando combinado para configurar y ejecutar el servidor:
   ```bash
   source .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt && python manage.py makemigrations && python manage.py migrate && python manage.py runserver
## Gunicorn

Solución para producción:
Para implementar tu aplicación en un entorno de producción, necesitas usar un servidor WSGI o ASGI como Gunicorn, uWSGI, o Daphne junto con un servidor web como Nginx o Apache. Aquí tienes los pasos básicos:

1. Instala Gunicorn:
   ```bash
   pip install gunicorn
2. Ejecuta Gunicorn:
   ```bash
   gunicorn config.wsgi:application --bind 0.0.0.0:8000
3. Configura un servidor web (como Nginx) para manejar solicitudes y servir archivos estáticos.
Asegúrate de que DEBUG esté en False en tu archivo settings.py (ya lo tienes configurado correctamente).

4. Configura ALLOWED_HOSTS con los dominios o direcciones IP permitidas para tu aplicación:
   ALLOWED_HOSTS = ['tu-dominio.com', 'www.tu-dominio.com']
5. Usa HTTPS y configura correctamente los certificados SSL.


## Nginx

1. Instalar Nginx
   ```bash
   sudo apt-get update && sudo apt-get install -y nginx
2. Crea archivo:
   ```bash
   sudo nano /etc/nginx/site-available/api_bank
3. Crea un archivo de configuración para tu aplicación en /etc/nginx/sites-available/tu_app:
   ```bash
   server {
   listen 80;
   server_name tu-dominio.com www.tu-dominio.com;

   location = /favicon.ico { access_log off; log_not_found off; }
   location /static/ {
      root /ruta/a/tu/proyecto; # Cambia esto por la ruta a tus archivos estáticos
   }

   location / {
      proxy_pass http://127.0.0.1:8000; # Gunicorn escucha en este puerto
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto $scheme;
   }
}


4. Habilita la configuración 
Crea un enlace simbólico para habilitar la configuración:
   ```bash
   sudo ln -s /etc/nginx/sites-available/api_bank /etc/nginx/sites-enabled/
5. Verifica y reinicia Nginx
Verifica que la configuración sea válida:
   ```bash
   sudo nginx -t
6. Si no hay errores, reinicia Nginx:
   ```bash
   sudo systemctl restart nginx
7. Configura archivos estáticos en Django. Asegúrate de haber recopilado los archivos estáticos en tu proyecto:
   ```bash
   python manage.py collectstatic
8. Prueba tu configuración
Accede a tu dominio o dirección IP en el navegador para verificar que todo funcione correctamente.

Con esto, Nginx manejará las solicitudes y servirá los archivos estáticos, mientras que Gunicorn ejecutará tu aplicación Django.


## Choices
     RJCT = "RJCT", "Rechazada"
     RCVD = "RCVD", "Recibida"
     ACCP = "ACCP", "Aceptada"
     ACTC = "ACTC", "Validación técnica aceptada"
     ACSP = "ACSP", "Acuerdo aceptado en proceso"
     ACSC = "ACSC", "Acuerdo aceptado completado"
     ACWC = "ACWC", "Aceptado con cambio"
     ACWP = "ACWP", "Aceptado con pendiente"
     ACCC = "ACCC", "Verificación de crédito aceptada"
     CANC = "CANC", "Cancelada"
     PDNG = "PDNG", "Pendiente"
