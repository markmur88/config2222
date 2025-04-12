from collections import defaultdict
import os

# Función para leer un archivo y devolver un diccionario
def leer_archivo(ruta_archivo: str) -> dict:
    datos = {}
    with open(ruta_archivo, "r") as archivo:
        for linea in archivo:
            clave, valor = linea.strip().split(": ")
            datos[clave] = valor
    return datos

# Función para combinar varios archivos en un diccionario
def combinar_archivos_en_diccionario(ruta_directorio: str) -> dict:
    diccionario_combinado = defaultdict(list)
    
    # Recorrer todos los archivos en el directorio
    for nombre_archivo in os.listdir(ruta_directorio):
        ruta_archivo = os.path.join(ruta_directorio, nombre_archivo)
        if os.path.isfile(ruta_archivo) and nombre_archivo.endswith(".txt"):
            datos = leer_archivo(ruta_archivo)
            for clave, valor in datos.items():
                diccionario_combinado[clave].append(valor)
    
    return dict(diccionario_combinado)

# Ruta del directorio que contiene los archivos
ruta_directorio = "ruta/al/directorio"

# Generar el diccionario combinado
diccionario_final = combinar_archivos_en_diccionario(ruta_directorio)
print(diccionario_final) 