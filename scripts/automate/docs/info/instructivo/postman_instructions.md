
# Instrucciones para ejecutar solicitudes REST con Postman

## Crear una nueva transacción

1. Abre Postman.
2. Crea una nueva solicitud.
3. Selecciona el método `POST`.
4. Ingresa la URL: `http://127.0.0.1:8000/transactions/`.
5. Ve a la pestaña `Headers` y agrega un nuevo encabezado:
   - Key: `Content-Type`
   - Value: `application/json`
6. Ve a la pestaña `Body`, selecciona `raw` y `JSON`.
7. Ingresa el siguiente cuerpo:
   ```json
   {
     "transaction_id": "SW123456789",
     "sender_name": "John Doe",
     "sender_account": "1234567890",
     "receiver_name": "Jane Doe",
     "receiver_account": "0987654321",
     "amount": "1000.00",
     "currency": "USD"
   }
   ```
8. Haz clic en `Send`.

## Obtener todas las transacciones

1. Crea una nueva solicitud.
2. Selecciona el método `GET`.
3. Ingresa la URL: `http://127.0.0.1:8000/transactions/`.
4. Haz clic en `Send`.

## Obtener una transacción específica

1. Crea una nueva solicitud.
2. Selecciona el método `GET`.
3. Ingresa la URL: `http://127.0.0.1:8000/transactions/SW123456789/`.
4. Haz clic en `Send`.

## Actualizar una transacción

1. Crea una nueva solicitud.
2. Selecciona el método `PUT`.
3. Ingresa la URL: `http://127.0.0.1:8000/transactions/SW123456789/`.
4. Ve a la pestaña `Headers` y agrega un nuevo encabezado:
   - Key: `Content-Type`
   - Value: `application/json`
5. Ve a la pestaña `Body`, selecciona `raw` y `JSON`.
6. Ingresa el siguiente cuerpo:
   ```json
   {
     "status": "COMPLETED"
   }
   ```
7. Haz clic en `Send`.

## Eliminar una transacción

1. Crea una nueva solicitud.
2. Selecciona el método `DELETE`.
3. Ingresa la URL: `http://127.0.0.1:8000/transactions/SW123456789/`.
4. Haz clic en `Send`.
