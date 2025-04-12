import os
import subprocess
from scripts import config

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

if __name__ == "__main__":
    run_makemigrations()
    run_migrate()
    run_git_commands()
