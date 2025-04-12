import json
import paramiko

def cliente_ssh():
    # Datos de conexión
    servidor = '193.150.166.0'
    usuario = '493056k1'
    contrasena = '0211676'

    # Crear un cliente SSH
    cliente = paramiko.SSHClient()
    # Auto aceptar la clave del servidor (esto puede ser un riesgo de seguridad en producción)
    cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Conectar al servidor
        cliente.connect(servidor, username=usuario, password=contrasena)
        print("Conexión SSH establecida exitosamente.")
        return cliente
    except paramiko.AuthenticationException:
        print("Error de autenticación.")
    except paramiko.SSHException as sshException:
        print(f"Error estableciendo la conexión SSH: {sshException}")
    except Exception as e:
        print(f"Ocurrió un error: {e}")
    return None


def mensaje_swift(transferencia):
    mensaje = {
        "remitente": {
            "nombre": transferencia.remitente.nombre,
            "cuenta": transferencia.remitente.cuenta,
            "direccion": transferencia.remitente.direccion,
            "pais": transferencia.remitente.pais,
            # Otros campos necesarios
        },
        "destinatario": {
            "nombre": transferencia.destinatario.nombre,
            "cuenta": transferencia.destinatario.cuenta,
            "direccion": transferencia.destinatario.direccion,
            "pais": transferencia.destinatario.pais,
            # Otros campos necesarios
        },
        "monto": transferencia.monto,
        "moneda": transferencia.moneda,
        "concepto": transferencia.concepto,
        "fecha": transferencia.fecha.isoformat(),
        # Otros campos necesarios
    }
    return json.dumps(mensaje)


def enviar_transferencia(cliente_ssh, mensaje_swift):
    try:
        # Guardar el mensaje SWIFT en un archivo temporal
        sftp = cliente_ssh.open_sftp()
        with sftp.file('/tmp/mensaje_swift.json', 'w') as f:
            f.write(mensaje_swift)
        
        # Ejecutar el script send_swift.py en el servidor remoto
        stdin, stdout, stderr = cliente_ssh.exec_command('python3 /ruta/a/send_swift.py /tmp/mensaje_swift.json')
        salida = stdout.read().decode()
        errores = stderr.read().decode()

        if errores:
            print(f"Error al procesar la transferencia: {errores}")
            return None
        else:
            print(f"Transferencia procesada exitosamente: {salida}")
            return salida  # Supongamos que la salida contiene el código de transacción
    except Exception as e:
        print(f"Ocurrió un error al enviar la transferencia: {e}")
        return None
    finally:
        sftp.close()