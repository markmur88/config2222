import os
import shutil
import subprocess
import ipaddress
import time
from datetime import datetime  # Importar módulo para manejar fecha y hora

def check_tools():
    tools = ["nc", "telnet", "ssh", "hydra", "medusa", "john", "hashcat", "ping", "nmap"]
    missing_tools = [tool for tool in tools if not shutil.which(tool)]
    if missing_tools:
        print(f"Las siguientes herramientas no están instaladas: {', '.join(missing_tools)}")
        print("Por favor, instálelas antes de continuar.")
        exit(1)

def get_ip_range():
    ip_start = input("Ingrese IP Ini: ")
    ip_end = input("Ingrese IP Fin: ")
    return ipaddress.summarize_address_range(ipaddress.IPv4Address(ip_start), ipaddress.IPv4Address(ip_end))

def get_port_range():
    port_start = int(input("Ingrese puerto Ini: "))
    port_end = int(input("Ingrese puerto Fin: "))
    return range(port_start, port_end + 1)

def get_file_locations():
    users_file = input("Ingrese la ubicación del archivo de usuarios: ")
    passwords_file = input("Ingrese la ubicación del archivo de passwords: ")
    return users_file, passwords_file

def get_selected_tools():
    tools = {
        "1": "nc", "2": "telnet", "3": "ssh", "4": "hydra", "5": "medusa",
        "6": "john", "7": "hashcat", "8": "ping", "9": "nmap"
    }
    print("Herramientas disponibles:")
    for key, tool in tools.items():
        print(f"{key}: {tool}")
    selected = input("Ingrese los números de las herramientas a usar (separados por espacio): ").split()
    return [tools[t] for t in selected if t in tools]

def scan_network(ip_range, port_range, users_file, passwords_file, selected_tools, report_file):
    cache = {}  # Diccionario para almacenar los resultados en caché
    with open(report_file, "w") as report:
        # Escribir la fecha y hora al inicio del informe
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report.write(f"Informe de escaneo - Fecha y hora: {timestamp}\n\n")
        
        for ip in ip_range:
            print(f"Escaneando IP: {ip}")
            report.write(f"Escaneando IP: {ip}\n")
            
            if subprocess.run(["ping", "-c", "1", "-W", "30", str(ip)], stdout=subprocess.DEVNULL).returncode != 0:
                print(f"Error: {ip} no responde")
                report.write(f"Error: {ip} no responde\n")
                cache[ip] = {"status": "no responde"}
                continue
            
            cache[ip] = {"status": "activo", "puertos": {}}
            for port in port_range:
                print(f"Escaneando puerto {port} en {ip}")
                report.write(f"Escaneando puerto {port} en {ip}\n")
                
                cache[ip]["puertos"][port] = {}
                for tool in selected_tools:
                    cmd = {
                        "nc": ["nc", "-zv", str(ip), str(port)],
                        "telnet": ["telnet", str(ip), str(port)],
                        "ssh": ["ssh", "-o", "BatchMode=yes", f"{ip}", "-p", str(port)],
                        "hydra": ["hydra", "-L", users_file, "-P", passwords_file, str(ip), "ssh", "-s", str(port)],
                        "medusa": ["medusa", "-h", str(ip), "-U", users_file, "-P", passwords_file, "-M", "ssh", "-n", str(port)],
                        "john": ["john", passwords_file, "--format=raw-md5", "--show"],
                        "hashcat": ["hashcat", "-m", "0", passwords_file, "--attack-mode", "3"],
                        "ping": ["ping", "-c", "4", str(ip)],
                        "nmap": ["nmap", "-p", str(port), str(ip)]
                    }
                    
                    result = subprocess.run(cmd[tool], capture_output=True, text=True)
                    cache[ip]["puertos"][port][tool] = result.stdout.strip()
                    report.write(result.stdout + "\n")
        
        # Imprimir resultados de la caché en el informe
        report.write("\nResumen del escaneo:\n")
        for ip, data in cache.items():
            report.write(f"\nIP: {ip}\n")
            report.write(f"Estado: {data['status']}\n")
            if data["status"] == "activo":
                for port, tools in data["puertos"].items():
                    report.write(f"  Puerto {port}:\n")
                    for tool, output in tools.items():
                        report.write(f"    {tool}: {output}\n")

def main():
    check_tools()
    ip_range = get_ip_range()
    port_range = get_port_range()
    users_file, passwords_file = get_file_locations()
    selected_tools = get_selected_tools()
    
    # Crear la carpeta 'reports' si no existe
    report_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(report_dir, exist_ok=True)
    
    # Incluir fecha y hora en el nombre del archivo de reporte
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(report_dir, f"reporte_{timestamp}.txt")
    print(f"El informe se guardará en: {report_file}")
    
    scan_network(ip_range, port_range, users_file, passwords_file, selected_tools, report_file)
    print(f"Escaneo completado. Informe guardado en: {report_file}")

if __name__ == "__main__":
    main()
