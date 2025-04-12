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

2. Recopila los archivos estáticos:
   ```bash
   python manage.py collectstatic

3. Inicia el servidor de desarrollo:
   ```bash
   python manage.py runserver

4. Comando combinado para configurar y ejecutar el servidor:
   ```bash
   source .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt && python manage.py makemigrations && python manage.py migrate && python manage.py runserver

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
