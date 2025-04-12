import socket
import concurrent.futures
from ipaddress import ip_network
from datetime import datetime
import os
from typing import List

# Definir el directorio base dinámicamente
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "escaneos")
os.makedirs(BASE_DIR, exist_ok=True)

# Leer archivo de diccionario
def leer_diccionario(ruta_archivo: str) -> List[str]:
    try:
        with open(ruta_archivo, "r") as f:
            return [linea.strip() for linea in f.readlines() if not linea.startswith("#")]
    except Exception as e:
        print(f"Error al leer el archivo {ruta_archivo}: {e}")
        return []

# Definir el rango de direcciones IP
ip_range = ip_network("193.150.166.0")

# Leer servidores desde el archivo correspondiente
ruta_diccionario = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diccionarios/diccionarios/servidores")
servidores = leer_diccionario(ruta_diccionario)

# Pedir la IP a escanear
print("Seleccione la IP a escanear:")
for i, servidor in enumerate(servidores):
    print(f"{i + 1}. {servidor.split(': ')[1]}")
seleccion = int(input("Ingrese el número correspondiente a la IP: ")) - 1
ip_to_scan = servidores[seleccion].split(": ")[1]

# Pedir el rango adicional de puertos a escanear
start_port = int(input("Ingrese el puerto inicial del rango adicional: "))
end_port = int(input("Ingrese el puerto final del rango adicional: "))

# Los 1000 puertos más comunes
common_ports = [
    22, # SSH
    80, # HTTP
    443, # HTTPS
    445, # SMB
    3389, # RDP
    3306, # MySQL
    1433, # MSSQL
    1521, # Oracle
    27017, # MongoDB
    6379, # Redis
    5432, # PostgreSQL
    8080, # HTTP
    8081, # HTTP
    8443, # HTTPS
    8888, # HTTP
    9090, # HTTP
    # Puedes agregar más puertos según lo necesites
] + list(range(start_port, end_port + 1))

# Lista para almacenar los puertos abiertos encontrados
open_ports = []

# Función para escanear un puerto específico en una IP
def scan_port(ip, port):
    try:
        # Crear un socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Establecer un tiempo de espera de 1 segundo
            s.settimeout(1)
            # Intentar conectar al puerto
            result = s.connect_ex((ip, port))
            if result == 0:
                print(f"Puerto {port} abierto en {ip}")
                open_ports.append((ip, port))
    except socket.error:
        pass

# Función para escanear todos los puertos en una IP
def scan_ip(ip):
    for port in common_ports:
        scan_port(ip, port)

# Función para escanear todas las IPs en el rango
def scan_range():
    # Usar ThreadPoolExecutor para escanear las IPs en paralelo
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        # Escanear la dirección IP especificada
        executor.map(scan_ip, [ip_to_scan])

# Función para comparar los puertos escaneados con los listados
def compare_ports():
    scanned_ports = set(port for ip, port in open_ports)
    listed_ports = set(common_ports)
    missing_ports = listed_ports - scanned_ports
    print("\nComparación de puertos:")
    print(f"Puertos listados no encontrados: {sorted(missing_ports)}")

# Función para escribir los resultados en un archivo txt
def write_results():
    filename = os.path.join(BASE_DIR, f"scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(filename, "w") as file:
        file.write(f"Fecha y hora de ejecución: {datetime.now()}\n")
        file.write(f"IP escaneada: {ip_to_scan}\n")
        file.write("Resultados del escaneo:\n")
        for ip, port in open_ports:
            file.write(f"IP: {ip}, Puerto: {port}\n")
        file.write("\nComparación de puertos:\n")
        scanned_ports = set(port for ip, port in open_ports)
        listed_ports = set(common_ports)
        missing_ports = listed_ports - scanned_ports
        file.write(f"Puertos listados no encontrados: {sorted(missing_ports)}\n")

# Ejecutar el escaneo
if __name__ == "__main__":
    print("Iniciando el escaneo de puertos...")
    scan_range()
    print("Escaneo completo.")
    compare_ports()
    write_results()
