import subprocess
import os
import logging
import sys
import time

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEYS_DIR = os.path.join(BASE_DIR, "keys")  # Actualizar ruta

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, "logs", "generar_claves_ssh.log")),
        logging.StreamHandler(sys.stdout)
    ],
)
logger = logging.getLogger(__name__)

# Configuración de errores
error_logger = logging.getLogger("error_logger")
error_logger.addHandler(logging.FileHandler(os.path.join(BASE_DIR, "logs", "errors.log")))

# Función para abrir una terminal y ejecutar un comando
def abrir_terminal(comando: str, titulo: str, password: str = None) -> None:
    try:
        logger.info(f"Iniciando: {titulo}")
        if password:
            comando = f"echo {password} | sudo -S {comando}"
        proceso = subprocess.Popen(comando, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            stdout, stderr = proceso.communicate(timeout=30)
            if proceso.returncode == 0:
                logger.info(f"Comando ejecutado correctamente: {titulo}")
            else:
                error_logger.error(f"Error al ejecutar el comando: {stderr.decode().strip()}")
        except subprocess.TimeoutExpired:
            proceso.kill()
            stdout, stderr = proceso.communicate()
            error_logger.error(f"El comando '{titulo}' excedió el tiempo de espera y fue terminado.")
    except Exception as e:
        error_logger.error(f"Error al ejecutar el comando: {e}")

# Función para generar claves SSH
def generar_claves_ssh(archivo_claves: str, password: str) -> None:
    if not os.path.exists(archivo_claves):
        comando = f"ssh-keygen -t rsa -b 4096 -f {archivo_claves} -N ''"
        abrir_terminal(comando, "Generar Claves SSH", password)
        logger.info(f"Claves SSH generadas en {archivo_claves}")
    else:
        logger.warning(f"Las claves SSH ya existen en {archivo_claves}")

# Función principal
def main() -> None:
    logger.info("Iniciando script de generación de claves SSH...")
    
    archivo_claves = os.path.join(KEYS_DIR, "id_rsa")
    password = "Ptf8454Jd55"  # Contraseña para sudo
    generar_claves_ssh(archivo_claves, password)
    time.sleep(2)  # Esperar un momento para que se generen las claves

    logger.info("Script de generación de claves SSH completado.")

if __name__ == "__main__":
    main()
