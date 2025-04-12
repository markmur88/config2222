# Campos para enviar por Postman

## URL de la solicitud
- **Método**: GET
- **URL**: `https://api.db.com:443/gw/dbapi/banking/transactions/v2`

## Encabezados (Headers)
- **Content-Type**: application/json
- **Authorization**: Bearer `tu-token-de-autorización`
- **Correlation-Id**: `tu-correlation-id` (opcional)

## Parámetros de Consulta (Query Parameters)
### Campos Requeridos
- **iban**: IBAN que representa una cuenta del usuario actual. Debe tener entre 5 y 34 caracteres y seguir el patrón `[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}`.

### Campos Opcionales
- **currencyCode**: Código de moneda ISO 4217 Alpha 3. Debe seguir el patrón `[A-Z]{3}`.
- **bookingDateFrom**: Fecha de reserva de la transacción original en formato ISO 8601 (YYYY-MM-DD).
- **bookingDateTo**: Fecha de reserva hasta la cual se buscarán las transacciones en formato ISO 8601 (YYYY-MM-DD).
- **sortBy**: Orden de clasificación de las transacciones. Valores soportados: 'bookingDate[ASC]' o 'bookingDate[DESC]'. Por defecto: 'bookingDate[ASC]'.
- **limit**: Límite de recursos por solicitud/página. Máximo: 200, Mínimo: 0, Por defecto: 10.
- **offset**: Página a devolver. Mínimo: 0, Por defecto: 0.

## Ejemplo de Cuerpo de Solicitud
```json
{
  "iban": "DE75440700240010581700",
  "currencyCode": "EUR",
  "bookingDateFrom": "2025-02-22",
  "bookingDateTo": "2025-02-22",
  "sortBy": "bookingDate[ASC]",
  "limit": 10,
  "offset": 0
}
```

## Instrucciones para Postman

1. **URL**: En la pestaña "Params", ingresa la URL de la solicitud.
2. **Headers**: En la pestaña "Headers", agrega los encabezados necesarios:
   - `Content-Type`: application/json
   - `Authorization`: Bearer `tu-token-de-autorización`
   - `Correlation-Id`: `tu-correlation-id` (opcional)
3. **Params**: En la pestaña "Params", agrega los parámetros de consulta necesarios:
   - `iban`: `DE75440700240010581700`
   - `currencyCode`: `EUR`
   - `bookingDateFrom`: `2025-02-22`
   - `bookingDateTo`: `2025-02-22`
   - `sortBy`: `bookingDate[ASC]`
   - `limit`: `10`
   - `offset`: `0`
