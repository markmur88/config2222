import os
import subprocess
from pathlib import Path
from datetime import datetime  # Importar datetime

# Definir BASE_DIR
BASE_DIR = Path(__file__).resolve().parent
 
def run_makemigrations():
    os.system('python manage.py makemigrations')

def run_migrate():
    os.system('python manage.py migrate')

def run_git_commands():
    try:
        subprocess.run(['git', 'add', '.'], check=True)
        # Crear un mensaje de commit con la fecha y hora actual
        commit_message = f"Auto commit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        subprocess.run(['git', 'push'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar los comandos de Git: {e}")

if __name__ == "__main__":
    run_makemigrations()
    run_migrate()
    run_git_commands()
    os.system('clear')  # Limpiar la terminal
