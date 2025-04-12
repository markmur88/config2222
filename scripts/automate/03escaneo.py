import socket
import concurrent.futures
from ipaddress import ip_network
from datetime import datetime
import os
from typing import List
import ipaddress

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

# Eliminar la lectura de servidores desde el archivo de diccionario
# ruta_diccionario = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diccionarios/diccionarios/servidores")
# servidores = leer_diccionario(ruta_diccionario)

# Eliminar la selección de IP desde el diccionario
# print("Seleccione la IP a escanear:")
# for i, servidor in enumerate(servidores):
#     print(f"{i + 1}. {servidor.split(': ')[1]}")
# seleccion = int(input("Ingrese el número correspondiente a la IP: ")) - 1
# ip_to_scan = servidores[seleccion].split(": ")[1]

# Eliminar la solicitud de IP específica
# ip_to_scan = input("Ingrese la IP a escanear: ")

# Pedir el puerto a escanear
# port_to_scan = int(input("Ingrese el puerto a escanear: "))

# Pedir el rango de direcciones IP a escanear
start_ip = input("Ingrese la IP Ini del rango a escanear: ")
end_ip = input("Ingrese la IP Fin del rango a escanear: ")

# Validar y generar el rango de IPs
try:
    ip_range = list(ipaddress.summarize_address_range(ipaddress.IPv4Address(start_ip), ipaddress.IPv4Address(end_ip)))
except ValueError as e:
    print(f"Error en el rango de IPs: {e}")
    exit(1)

# Pedir el rango de puertos a escanear
start_port = int(input("Ingrese el puerto Ini del rango a escanear: "))
end_port = int(input("Ingrese el puerto Fin del rango a escanear: "))

# Validar el rango de puertos
if start_port > end_port or start_port < 1 or end_port > 65535:
    print("Rango de puertos inválido. Asegúrese de que el rango sea válido (1-65535).")
    exit(1)

# Generar la lista de puertos a escanear
common_ports = list(range(start_port, end_port + 1))

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
    # Ajustar para escanear todos los puertos en el rango
    for port in common_ports:
        scan_port(ip, port)

# Función para escanear todas las IPs en el rango
def scan_range():
    # Usar ThreadPoolExecutor para escanear las IPs en paralelo
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        # Generar todas las IPs en el rango y escanearlas
        all_ips = [str(ip) for subnet in ip_range for ip in subnet]
        executor.map(scan_ip, all_ips)

# Función para comparar los puertos escaneados con los listados
def compare_ports():
    all_ips = [str(ip) for subnet in ip_range for ip in subnet]
    scanned_ports_by_ip = {ip: set() for ip in all_ips}
    
    # Registrar los puertos encontrados por IP
    for ip, port in open_ports:
        scanned_ports_by_ip[ip].add(port)
    
    # Verificar puertos no encontrados por IP
    print("\nPuertos no encontrados por IP:")
    for ip in all_ips:
        missing_ports = set(common_ports) - scanned_ports_by_ip[ip]
        if missing_ports:
            print(f"IP: {ip}, Puertos no encontrados: {sorted(missing_ports)}")
    
    # Verificar IPs no escaneadas
    scanned_ips = set(ip for ip, port in open_ports)
    missing_ips = set(all_ips) - scanned_ips
    if missing_ips:
        print("\nIPs no encontradas:")
        for ip in sorted(missing_ips):
            print(ip)
    else:
        print("\nTodas las IPs fueron encontradas.")

# Función para escribir los resultados en un archivo txt
def write_results():
    filename = os.path.join(BASE_DIR, f"scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(filename, "w") as file:
        file.write(f"Fecha y hora de ejecución: {datetime.now()}\n")
        file.write(f"Rango de puertos escaneados: {start_port}-{end_port}\n")
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
