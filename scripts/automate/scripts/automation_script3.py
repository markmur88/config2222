import subprocess
import json
import time
import os
import logging
import sys
import socket
import concurrent.futures
from collections import defaultdict
from ipaddress import ip_network, ip_address
from typing import Dict, List, Optional  # Agregar Optional

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "../config", "config.json")  # Actualizar ruta
CONFIG_BASE_PATH = os.path.join(BASE_DIR, "../config", "config_base.json")  # Actualizar ruta
LOGS_DIR = os.path.join(BASE_DIR, "logs")
KEYS_DIR = os.path.join(BASE_DIR, "keys")
DICCIONARIOS_DIR = os.path.join(BASE_DIR, "diccionarios")

# Crear directorio si no existe
def crear_directorio_si_no_existe(directorio: str) -> None:
    if not os.path.exists(directorio):
        os.makedirs(directorio)
        logger.info(f"Directorio creado: {directorio}")

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

# Crear directorio de logs si no existe
crear_directorio_si_no_existe(LOGS_DIR)

# Configuración de errores
error_logger = logging.getLogger("error_logger")
error_logger.addHandler(logging.FileHandler(os.path.join(LOGS_DIR, "errors.log")))

# Cargar configuración base
def cargar_config_base() -> Optional[Dict]:
    try:
        with open(CONFIG_BASE_PATH, "r") as f:
            config = json.load(f)
        logger.info("Configuración base cargada correctamente.")
        return config
    except Exception as e:
        error_logger.error(f"Error al cargar la configuración base: {e}")
        return None

# Generar lista de IPs a partir de rangos
def generar_ips(rangos_ip: List[str]) -> List[str]:
    ips = []
    for rango in rangos_ip:
        if "-" in rango:
            inicio, fin = rango.split("-")
            red = ip_network(inicio, strict=False)
            for ip in red.hosts():
                if str(ip).endswith(fin):
                    break
                ips.append(str(ip))
        else:
            ips.append(rango)
    return ips

# Función para escanear un puerto específico en una IP
def scan_port(ip, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((ip, port))
            if result == 0:
                logger.info(f"Puerto {port} abierto en {ip}")
    except socket.error:
        pass

# Función para escanear todos los puertos en una IP
def scan_ip(ip):
    common_ports = [22]  # Puedes agregar más puertos según lo necesites
    for port in common_ports:
        scan_port(ip, port)

# Función para escanear todas las IPs en el rango
def scan_range(ip_range):
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(scan_ip, (str(ip) for ip in ip_network(ip_range).hosts()))

# Leer archivo de diccionario
def leer_diccionario(ruta_archivo: str) -> List[str]:
    try:
        with open(ruta_archivo, "r") as f:
            return [linea.strip() for linea in f.readlines()]
    except Exception as e:
        error_logger.error(f"Error al leer el archivo {ruta_archivo}: {e}")
        return []

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
def abrir_terminal(comando: str, titulo: str) -> None:
    try:
        subprocess.run(["gnome-terminal", "--title", titulo, "--", "bash", "-c", comando + "; exec bash"], check=True)
        logger.info(f"Terminal abierta: {titulo}")
    except subprocess.CalledProcessError as e:
        error_logger.error(f"Error al abrir la terminal: {e}")

# Función para verificar si una herramienta está instalada
def verificar_herramienta(herramienta: str) -> bool:
    try:
        subprocess.run([herramienta, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        logger.info(f"{herramienta} está instalada.")
        return True
    except subprocess.CalledProcessError:
        error_logger.error(f"{herramienta} no está instalada.")
        return False

# Realizar pruebas de penetración con Hydra
def prueba_hydra(ip: str, usuario: str, contrasena: str, config: Dict) -> None:
    comando = f"hydra -l {usuario} -p {contrasena} {ip} ssh -V -t 4 -s {config['puerto_ssh']}"
    abrir_terminal(comando, f"Ataque Hydra a {ip}")
    logger.info(f"Iniciando ataque de Hydra en {ip} con usuario {usuario} y contraseña {contrasena}...")
    time.sleep(config["timeout_hydra"])
    enviar_transaccion(ip, usuario, contrasena, "conexion_exitosa")

# Función principal
def main() -> None:
    logger.info("Iniciando script de automatización...")
    
    # Cargar configuración base
    config_base = cargar_config_base()
    if not config_base:
        error_logger.error("No se pudo cargar la configuración base. Verifica el archivo config_base.json.")
        sys.exit(1)
    
    # Escanear rangos de IP
    for rango_ip in config_base["rangos_ip"]:
        scan_range(rango_ip)
    
    # Generar lista de IPs
    ips = generar_ips(config_base["rangos_ip"])
    logger.info(f"IPs generadas: {ips}")
    
    # Leer diccionarios de usuarios y contraseñas
    usuarios = leer_diccionario(os.path.join(BASE_DIR, config_base["archivo_usuarios"]))  # Actualizar ruta
    contrasenas = leer_diccionario(os.path.join(BASE_DIR, config_base["archivo_contrasenas"]))  # Actualizar ruta
    
    # Verificar dependencias
    herramientas = ["ssh-keygen", "nmap", "hydra", "ssh"]
    for herramienta in herramientas:
        if not verificar_herramienta(herramienta):
            error_logger.error(f"Falta la herramienta: {herramienta}. Instálala antes de continuar.")
            sys.exit(1)
    
    # Realizar pruebas de penetración
    for ip in ips:
        for usuario in usuarios:
            for contrasena in contrasenas:
                prueba_hydra(ip, usuario, contrasena, config_base)
                time.sleep(2)  # Esperar un momento entre pruebas

    logger.info("Script completado.")

if __name__ == "__main__":
    main()

