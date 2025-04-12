import csv
import os
from collections import defaultdict

# Función para leer un archivo CSV
def leer_csv(ruta_archivo: str) -> dict:
    with open(ruta_archivo, "r") as archivo:
        lector = csv.DictReader(archivo)
        return next(lector)  # Solo lee la primera fila

# Función para combinar varios archivos CSV en un diccionario
def combinar_csv_en_diccionario(ruta_directorio: str) -> dict:
    diccionario_combinado = defaultdict(list)
    
    # Recorrer todos los archivos en el directorio
    for nombre_archivo in os.listdir(ruta_directorio):
        ruta_archivo = os.path.join(ruta_directorio, nombre_archivo)
        if os.path.isfile(ruta_archivo) and nombre_archivo.endswith(".csv"):
            datos = leer_csv(ruta_archivo)
            for clave, valor in datos.items():
                diccionario_combinado[clave].append(valor)
    
    return dict(diccionario_combinado)

# Ruta del directorio que contiene los archivos CSV
ruta_directorio = "ruta/al/directorio"

# Generar el diccionario combinado
diccionario_final = combinar_csv_en_diccionario(ruta_directorio)
print(diccionario_final) 