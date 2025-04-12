import os
import subprocess
from scripts import config
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

def run_makemigrations():
    try:
        subprocess.run(['python', 'manage.py', 'makemigrations'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar makemigrations: {e}")

def run_migrate():
    try:
        subprocess.run(['python', 'manage.py', 'migrate'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar migrate: {e}")

def run_git_commands():
    try:
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Auto commit'], check=True)
        subprocess.run(['git', 'push'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar los comandos de Git: {e}")

def run_server():
    try:
        cert_file = os.path.join(os.path.dirname(__file__), 'keys/cert.pem')
        key_file = os.path.join(os.path.dirname(__file__), 'keys/key.pem')
        subprocess.run([
            'gunicorn', '--config', 'gunicorn_config.py', 'config.wsgi:application',
            '--certfile', cert_file, '--keyfile', key_file
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar el servidor: {e}")

if __name__ == "__main__":
    run_makemigrations()
    run_migrate()
    #run_git_commands()
    run_server()