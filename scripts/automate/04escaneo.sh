#!/bin/bash

# Función para solicitar un rango de IPs
read -p "Ingrese IP inicial: " IP_START
read -p "Ingrese IP final: " IP_END

# Función para solicitar un rango de puertos
read -p "Ingrese puerto inicial: " PORT_START
read -p "Ingrese puerto final: " PORT_END

# Ubicación de archivos de usuarios y passwords
read -p "Ingrese la ubicación del archivo de usuarios: " USERS_FILE
read -p "Ingrese la ubicación del archivo de passwords: " PASSWORDS_FILE

# Selección de herramientas
echo "Seleccione las herramientas a usar (separe con espacios):"
echo "1) Netcat  2) Telnet  3) SSH  4) Hydra  5) Medusa  6) John the Ripper  7) Hashcat  8) Ping  9) Nmap"
read -p "Ingrese los números de las herramientas: " TOOLS

# Solicitar ubicación para el informe final
read -p "Ingrese la ubicación para guardar el informe: " REPORT_FILE

# Convertir IPs en enteros para iteración
IFS=. read -r i1 i2 i3 i4 <<< "$IP_START"
IFS=. read -r f1 f2 f3 f4 <<< "$IP_END"
start_ip=$(( (i1 << 24) + (i2 << 16) + (i3 << 8) + i4 ))
end_ip=$(( (f1 << 24) + (f2 << 16) + (f3 << 8) + f4 ))

# Recorrer IPs dentro del rango
for ((ip=start_ip; ip<=end_ip; ip++)); do
    i1=$(( (ip >> 24) & 255 ))
    i2=$(( (ip >> 16) & 255 ))
    i3=$(( (ip >> 8) & 255 ))
    i4=$(( ip & 255 ))
    current_ip="$i1.$i2.$i3.$i4"
    echo "Escaneando IP: $current_ip" | tee -a "$REPORT_FILE"
    
    # Verificar si la IP responde en 30 segundos
    ping -c 1 -W 30 "$current_ip" &>/dev/null
    if [ $? -ne 0 ]; then
        echo "Error: $current_ip no responde" | tee -a "$REPORT_FILE"
        continue
    fi
    
    # Iterar sobre los puertos
    for ((port=PORT_START; port<=PORT_END; port++)); do
        echo "Escaneando puerto $port en $current_ip" | tee -a "$REPORT_FILE"
        
        for tool in $TOOLS; do
            case $tool in
                1) nc -zv "$current_ip" "$port" 2>&1 | tee -a "$REPORT_FILE" ;;
                2) telnet "$current_ip" "$port" 2>&1 | tee -a "$REPORT_FILE" ;;
                3) ssh -o BatchMode=yes "$current_ip" -p "$port" 2>&1 | tee -a "$REPORT_FILE" ;;
                4) hydra -L "$USERS_FILE" -P "$PASSWORDS_FILE" "$current_ip" ssh -s "$port" 2>&1 | tee -a "$REPORT_FILE" ;;
                5) medusa -h "$current_ip" -U "$USERS_FILE" -P "$PASSWORDS_FILE" -M ssh -n "$port" 2>&1 | tee -a "$REPORT_FILE" ;;
                6) john "$PASSWORDS_FILE" --format=raw-md5 --show 2>&1 | tee -a "$REPORT_FILE" ;;
                7) hashcat -m 0 "$PASSWORDS_FILE" --attack-mode 3 2>&1 | tee -a "$REPORT_FILE" ;;
                8) ping -c 4 "$current_ip" 2>&1 | tee -a "$REPORT_FILE" ;;
                9) nmap -p "$port" "$current_ip" 2>&1 | tee -a "$REPORT_FILE" ;;
            esac
        done
    done
done

echo "Escaneo completado. Informe guardado en: $REPORT_FILE"
