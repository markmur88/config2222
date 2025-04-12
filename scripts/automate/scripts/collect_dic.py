import csv
import json
import os
from collections import defaultdict


# Función para leer un archivo CSV
def leer_csv(ruta_archivo: str) -> dict:
    with open(ruta_archivo, "r", encoding="utf-8", errors="ignore") as archivo:
        lector = csv.DictReader(archivo)
        return next(lector)  # Solo lee la primera fila

# Función para leer un archivo JSON
def leer_json(ruta_archivo: str) -> dict:
    try:
        with open(ruta_archivo, "r", encoding="utf-8", errors="ignore") as archivo:
            return json.load(archivo)
    except json.JSONDecodeError as e:
        print(f"Error al decodificar JSON en {ruta_archivo}: {e}")
        return {}

# Función para leer un archivo de texto
def leer_txt(ruta_archivo: str) -> dict:
    datos = {}
    with open(ruta_archivo, "r", encoding="utf-8", errors="ignore") as archivo:
        for linea in archivo:
            try:
                clave, valor = linea.strip().split(": ", 1)
                datos[clave] = valor
            except ValueError:
                print(f"Línea con formato incorrecto en {ruta_archivo}: {linea.strip()}")
    return datos

# Función para leer un archivo sin extensión
def leer_sin_extension(ruta_archivo: str) -> dict:
    datos = {}
    with open(ruta_archivo, "r", encoding="utf-8", errors="ignore") as archivo:
        for linea in archivo:
            partes = linea.strip().split(": ", 1)  # Usar maxsplit=1
            if len(partes) == 2:
                clave, valor = partes
                datos[clave] = valor
    return datos

# Función para combinar varios archivos en un diccionario
def combinar_archivos_en_diccionario(ruta_directorio: str) -> dict:
    diccionario_combinado = defaultdict(list)
    
    # Recorrer todos los archivos y subcarpetas en el directorio
    for root, _, files in os.walk(ruta_directorio):
        for nombre_archivo in files:
            ruta_archivo = os.path.join(root, nombre_archivo)
            if os.path.isfile(ruta_archivo):
                if nombre_archivo.endswith(".csv"):
                    datos = leer_csv(ruta_archivo)
                elif nombre_archivo.endswith(".json"):
                    datos = leer_json(ruta_archivo)
                elif nombre_archivo.endswith(".txt"):
                    datos = leer_txt(ruta_archivo)
                else:
                    datos = leer_sin_extension(ruta_archivo)
                
                for clave, valor in datos.items():
                    diccionario_combinado[clave].append(valor)
    
    return dict(diccionario_combinado)

# Función para escribir un diccionario en un archivo de texto sin repetir valores
def escribir_diccionario_en_archivo(diccionario: dict, ruta_archivo: str) -> None:
    valores_escritos = set()
    with open(ruta_archivo, "w") as archivo:
        for clave, valores in diccionario.items():
            for valor in valores:
                if valor not in valores_escritos:
                    archivo.write(f"{clave}: {valor}\n")
                    valores_escritos.add(valor)

# Función para escribir valores específicos en archivos separados sin duplicados
def escribir_valores_especificos(diccionario: dict, ruta_usuarios: str, ruta_contraseñas: str) -> None:
    usuarios_escritos = set()
    contraseñas_escritas = set()
    
    with open(ruta_usuarios, "w") as archivo_usuarios, open(ruta_contraseñas, "w") as archivo_contraseñas:
        for clave, valores in diccionario.items():
            for valor in valores:
                valor = valor.split(": ", 1)[-1]  # Extraer el valor después de ": "
                if len(valor) <= 60:  # Limitar la longitud a 50 caracteres
                    if "User Name" in clave or "User ID" in clave:
                        if valor not in usuarios_escritos:
                            archivo_usuarios.write(f"{valor}\n")
                            usuarios_escritos.add(valor)
                    elif "PIN" in clave or "SSN" in clave:
                        if valor not in contraseñas_escritas:
                            archivo_contraseñas.write(f"{valor}\n")
                            contraseñas_escritas.add(valor)

# Función para escribir un diccionario general en un archivo de texto sin duplicados
def escribir_diccionario_general(diccionario: dict, ruta_archivo: str) -> None:
    valores_escritos = set()
    with open(ruta_archivo, "w") as archivo:
        for clave, valores in diccionario.items():
            for valor in valores:
                valor = valor.split(": ", 1)[-1]  # Extraer el valor después de ": "
                if len(valor) <= 50 and valor not in valores_escritos:  # Limitar la longitud a 50 caracteres
                    archivo.write(f"{valor}\n")
                    valores_escritos.add(valor)

# Ruta del directorio que contiene los archivos
ruta_directorio = "/home/markmur88/Documentos/automation_project/docs/info/analisis"

# Generar el diccionario combinado
diccionario_final = combinar_archivos_en_diccionario(ruta_directorio)

# Guardar los valores específicos en los archivos correspondientes
ruta_contraseñas = "/home/markmur88/Documentos/automation_project/diccionarios/contraseñas.txt"
ruta_usuarios = "/home/markmur88/Documentos/automation_project/diccionarios/usuarios.txt"
ruta_wordlist = "/home/markmur88/Documentos/automation_project/diccionarios/wordlist.txt"

escribir_valores_especificos(diccionario_final, ruta_usuarios, ruta_contraseñas)
escribir_diccionario_general(diccionario_final, ruta_wordlist)

print(diccionario_final)

