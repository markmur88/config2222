import subprocess
import json
import time
import os
import logging
import sys
from typing import Optional, Dict, List

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "../config", "config.json")  # Actualizar ruta
LOGS_DIR = os.path.join(BASE_DIR, "logs")
KEYS_DIR = os.path.join(BASE_DIR, "keys")

password = "Ptf8454Jd55"
    
# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "automation.log")),
        logging.StreamHandler(sys.stdout)
    ],
)
logger = logging.getLogger(__name__)

# Configuración de errores
error_logger = logging.getLogger("error_logger")
error_logger.addHandler(logging.FileHandler(os.path.join(LOGS_DIR, "errors.log")))

# Cargar configuración
def cargar_configuracion() -> Optional[Dict]:
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
        logger.info("Configuración cargada correctamente.")
        return config
    except Exception as e:
        error_logger.error(f"Error al cargar la configuración: {e}")
        return None

# Función para enviar un JSON de transacción
def enviar_transaccion(ip: str, usuario: str, clave: str, estado: str) -> None:
    transaccion = {
        "fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
        "ip_servidor": ip,
        "usuario": usuario,
        "clave": clave,
        "estado": estado
    }
    logger.info("Enviando transacción JSON:")
    logger.info(json.dumps(transaccion, indent=4))

# Función para abrir una terminal y ejecutar un comando
def abrir_terminal(comando: str, titulo: str, password: str = "Ptf8454Jd55") -> None:
    try:
        logger.info(f"Iniciando: {titulo}")
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

# Función para verificar si una herramienta está instalada
def verificar_herramienta(herramienta: str) -> bool:
    try:
        comando = f"echo {password} | sudo -S {herramienta} --version"
        resultado = subprocess.run(comando, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, timeout=10)
        logger.info(f"{herramienta} está instalada. Salida: {resultado.stdout.decode().strip()}")
        return True
    except subprocess.CalledProcessError as e:
        error_logger.error(f"{herramienta} no está instalada. Error: {e}")
        return False
    except subprocess.TimeoutExpired:
        error_logger.error(f"El comando para verificar {herramienta} excedió el tiempo de espera y fue terminado.")
        return False

# Leer archivo de diccionario
def leer_diccionario(ruta_archivo: str) -> List[str]:
    ruta_completa = os.path.join(BASE_DIR, "../diccionarios", ruta_archivo)
    try:
        with open(ruta_completa, "r") as f:
            return [linea.strip() for linea in f.readlines()]
    except Exception as e:
        error_logger.error(f"Error al leer el archivo {ruta_completa}: {e}")
        return []

# Función para escanear puertos
def escanear_puertos(config: Dict) -> None:
    comando = f"nmap -p 22 {config['ip_servidor']}"
    abrir_terminal(comando, "Escanear Puertos")
    logger.info(f"Escaneando puertos en {config['ip_servidor']}...")

# Función principal
def main() -> None:
    logger.info("Iniciando script de automatización...")
    
    # Cargar configuración
    config = cargar_configuracion()
    if not config:
        error_logger.error("No se pudo cargar la configuración. Verifica el archivo config.json.")
        sys.exit(1)
    
    # Contraseña para sudo
    password = "Ptf8454Jd55"
    
    # Verificar dependencias
    herramientas = ["nmap"]
    for herramienta in herramientas:
        if not verificar_herramienta(herramienta):
            error_logger.error(f"Falta la herramienta: {herramienta}. Instálala antes de continuar.")
            sys.exit(1)
    
    # Paso 1: Escanear puertos
    logger.info("Paso 1: Escanear puertos")
    escanear_puertos(config)
    time.sleep(2)  # Esperar un momento para el escaneo de puertos

    logger.info("Script completado.")

if __name__ == "__main__":
    main()