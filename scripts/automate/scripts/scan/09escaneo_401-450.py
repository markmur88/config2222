import socket
import concurrent.futures
from ipaddress import ip_network

# Definir el rango de direcciones IP
ip_range = ip_network("193.150.166.0")

# Los 1000 puertos más comunes
common_ports = [
    401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 449, 450,
    
    # Puedes agregar más puertos según lo necesites
]

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
        # Escanear todas las direcciones IP en el rango
        executor.map(scan_ip, (str(ip) for ip in ip_range.hosts()))

# Ejecutar el escaneo
if __name__ == "__main__":
    print("Iniciando el escaneo de puertos...")
    scan_range()
    print("Escaneo completo.")
