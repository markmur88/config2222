import os
import shutil
import subprocess
import ipaddress
import time

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
    selected = input("Ingrese los números de las herramientas a usar (separados por espacio): ").split()
    return [tools[t] for t in selected if t in tools]

def scan_network(ip_range, port_range, users_file, passwords_file, selected_tools, report_file):
    with open(report_file, "w") as report:
        for ip in ip_range:
            print(f"Escaneando IP: {ip}")
            report.write(f"Escaneando IP: {ip}\n")
            
            if subprocess.run(["ping", "-c", "1", "-W", "30", str(ip)], stdout=subprocess.DEVNULL).returncode != 0:
                print(f"Error: {ip} no responde")
                report.write(f"Error: {ip} no responde\n")
                continue
            
            for port in port_range:
                print(f"Escaneando puerto {port} en {ip}")
                report.write(f"Escaneando puerto {port} en {ip}\n")
                
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
                    report.write(result.stdout + "\n")

def main():
    check_tools()
    ip_range = get_ip_range()
    port_range = get_port_range()
    users_file, passwords_file = get_file_locations()
    selected_tools = get_selected_tools()
    report_file = input("Ingrese la ubicación para guardar el informe: ")
    
    scan_network(ip_range, port_range, users_file, passwords_file, selected_tools, report_file)
    print(f"Escaneo completado. Informe guardado en: {report_file}")

if __name__ == "__main__":
    main()
