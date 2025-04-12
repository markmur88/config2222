import socket
import concurrent.futures
from ipaddress import ip_network

# Definir el rango de direcciones IP
ip_range = ip_network("193.150.166.0")

# Los 1000 puertos más comunes
common_ports = [
    151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200,
    
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
