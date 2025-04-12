import os
import subprocess

def run_makemigrations():
    os.system('python manage.py makemigrations')

def run_migrate():
    os.system('python manage.py migrate')

if __name__ == "__main__":
    run_makemigrations()
    run_migrate()
