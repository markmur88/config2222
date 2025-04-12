import json
import os
from collections import defaultdict

# Función para leer un archivo JSON
def leer_json(ruta_archivo: str) -> dict:
    with open(ruta_archivo, "r") as archivo:
        return json.load(archivo)

# Función para combinar varios archivos JSON en un diccionario
def combinar_json_en_diccionario(ruta_directorio: str) -> dict:
    diccionario_combinado = defaultdict(list)
    
    # Recorrer todos los archivos en el directorio
    for nombre_archivo in os.listdir(ruta_directorio):
        ruta_archivo = os.path.join(ruta_directorio, nombre_archivo)
        if os.path.isfile(ruta_archivo) and nombre_archivo.endswith(".json"):
            datos = leer_json(ruta_archivo)
            for clave, valor in datos.items():
                diccionario_combinado[clave].append(valor)
    
    return dict(diccionario_combinado)

# Ruta del directorio que contiene los archivos JSON
ruta_directorio = "ruta/al/directorio"

# Generar el diccionario combinado
diccionario_final = combinar_json_en_diccionario(ruta_directorio)
print(diccionario_final) 