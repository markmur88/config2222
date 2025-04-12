import socket
import concurrent.futures
from ipaddress import ip_network
import paramiko
import random
import requests
from scripts.config import SWIFT_SETTINGS
from scripts.generated_token import access_token

# Definir el rango de direcciones IP
ip_range = ip_network("193.150.166.0")
ip = "193.150.166.0"
port = 22
username = "493056k1"
password =  "0211676"



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
 
# Función para conectarse a una IP específica usando SSH
def connect_ssh(ip, port, username, password):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        client.connect(ip, port=port, username=username, password=password)
        print(f"Conectado a {ip}:{port} exitosamente")
        
        # Realizar petición JSON
        url = SWIFT_SETTINGS['BANK_API_URL']
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        data = {
            "origin_iban": "DE86500700100925993805",
            "origin_bic": "DEUTDEFFXXX",
            "amount": 460000.00,
            "currency_code": "EUR",
            "counter_party_bank_name": "SANTANDER S.A.",
            "counter_party_account_number": "ES9400496103962716120773",
            "counter_party_name": "LEGALNET SYSTEMS SPAIN SL",
            "counter_party_bic": "BSCHESMMXXX",
            "payment_reference": "JN2DKYS-LNS-2",
            "transaction_date": "2025-03-07",
            "status": "PDNG",
            "uetr": "fe25c431-e658-4ca5-ae9f-ce73c1cb82dd",
            "additional_info": "Transaction processed successfully",
            "transaction_fee": 0,
            "processed_by": "System",
            "processed_date": "2025-03-07",
            "transaction_success": True
        }
        response = requests.post(url, headers=headers, json=data)
        print(f"Petición JSON enviada, respuesta: {response.status_code}")
        
        client.close()
    except paramiko.ssh_exception.SSHException as e:
        print(f"Error al conectar a {ip}:{port}: {e}")
    except paramiko.ssh_exception.SSHBannerError as e:
        print(f"Error de banner SSH al conectar a {ip}:{port}: {e}")
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
        connect_ssh(ip, port, SWIFT_SETTINGS['USERNAME'], SWIFT_SETTINGS['PIN'])
    else:
        print("No se encontraron IPs con puertos abiertos.")
