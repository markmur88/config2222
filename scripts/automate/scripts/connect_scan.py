import socket
import concurrent.futures
from ipaddress import ip_network
import paramiko
import random
import requests
import os

# Definir el directorio base
BASE_DIR = "/home/markmur88/Documentos/automation_project"
KEYS_DIR = os.path.join(BASE_DIR, 'keys')
os.makedirs(KEYS_DIR, exist_ok=True)



# Definir el rango de direcciones IP
ip_range = ip_network("193.150.166.0")

# Los 1000 puertos más comunes
common_ports = [
    22,
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
                return port
    except socket.error:
        pass
    return None

# Función para escanear todos los puertos en una IP
def scan_ip(ip):
    open_ports = []
    for port in common_ports:
        open_port = scan_port(ip, port)
        if open_port:
            open_ports.append(open_port)
    return open_ports

# Función para escanear todas las IPs en el rango
def scan_range():
    open_ips = {}
    # Usar ThreadPoolExecutor para escanear las IPs en paralelo
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        # Escanear todas las direcciones IP en el rango
        results = executor.map(scan_ip, (str(ip) for ip in ip_range.hosts()))
        for ip, open_ports in zip(ip_range.hosts(), results):
            if open_ports:
                open_ips[str(ip)] = open_ports
    return open_ips

# Función para generar una clave RSA si no existe
def generate_rsa_key(cert_path):
    key = paramiko.RSAKey.generate(2048)
    key.write_private_key_file(cert_path)
    return key

# Función para conectarse a una IP específica usando SSH
def connect_ssh(ip, port, username, password):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Buscar el certificado en KEYS_DIR
        cert_path = os.path.join(KEYS_DIR, 'cert')
        if not os.path.exists(cert_path):
            # Generar el certificado si no existe
            cert = generate_rsa_key(cert_path)
        else:
            cert = paramiko.RSAKey(filename=cert_path)
        
        client.get_host_keys().add(ip, 'ssh-rsa', cert)
        
        client.connect(ip, port=port, username=username, password=password)
        print(f"Conectado a {ip}:{port} exitosamente")
        
        # Enviar petición JSON
        #send_json_request(ip, port)
        
        client.close()
    except paramiko.ssh_exception.SSHException as e:
        print(f"Error al conectar a {ip}:{port}: {e}")
    except paramiko.ssh_exception.SSHBannerError as e:
        print(f"Error de banner SSH al conectar a {ip}:{port}: {e}")
    except paramiko.ssh_exception.SSHException as e:
        if "Error reading SSH protocol banner" in str(e):
            print(f"Error al leer el banner del protocolo SSH al conectar a {ip}:{port}: {e}")
        else:
            print(f"Error al conectar a {ip}:{port}: {e}")
    except socket.timeout:
        print(f"Error de tiempo de espera al conectar a {ip}:{port}")
    except ConnectionResetError:
        print(f"Conexión reiniciada por el par al conectar a {ip}:{port}")
    except Exception as e:
        print(f"Error inesperado al conectar a {ip}:{port}: {e}")

# Ejecutar el escaneo y la conexión
if __name__ == "__main__":
    print("Iniciando el escaneo de puertos...")
    open_ips = scan_range()
    print("Escaneo completo.")
    
    if open_ips:
        print("Intentando conectar a una IP con puerto abierto aleatoriamente...")
        ip = random.choice(list(open_ips.keys()))
        port = random.choice(open_ips[ip])
        connect_ssh(ip, port, "493069k1", "bar1588623")
    else:
        print("No se encontraron IPs con puertos abiertos.")
