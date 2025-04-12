# Campos para enviar por Postman

## URL de la solicitud
- **Método**: POST
- **URL**: `https://api.db.com:443/

gw/dbapi/banking/transactions/v2`

## Encabezados (Headers)
- **Content-Type**: application/json
- **Authorization**: Bearer `H858hfhg0ht40588hhfjpfhhd9944940jf`
- **Correlation-Id**: `tu-correlation-id` (opcional)

## Cuerpo de la Solicitud (Body)
### Campos Requeridos
- **iban**: IBAN que representa una cuenta del usuario actual. Debe tener entre 5 y 34 caracteres y seguir el patrón `[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}`.
- **amount**: Monto de la transacción. Debe ser un número positivo.
- **currencyCode**: Código de moneda ISO 4217 Alpha 3. Debe seguir el patrón `[A-Z]{3}`.
- **description**: Descripción de la transacción. Máximo 140 caracteres.

### Campos Opcionales
- **executionDate**: Fecha de ejecución de la transacción en formato ISO 8601 (YYYY-MM-DD).

## Ejemplo de Cuerpo de Solicitud
```json
{
  "iban": "DE75440700240010581700",
  "amount": 500000.00,
  "currencyCode": "EUR",
  "description": "JN2DKYS",
  "executionDate": "2025-02-23"
}
```

## Instrucciones para Postman

1. **URL**: En la pestaña "Params", ingresa la URL de la solicitud.
2. **Headers**: En la pestaña "Headers", agrega los encabezados necesarios:
   - `Content-Type`: application/json
   - `Authorization`: Bearer `tu-token-de-autorización`
   - `Correlation-Id`: `tu-correlation-id` (opcional)
3. **Body**: En la pestaña "Body", selecciona "raw" y "JSON", luego ingresa el cuerpo de la solicitud:
```json
{
  "iban": "DE75440700240010581700",
  "amount": 100.50,
  "currencyCode": "EUR",
  "description": "Pago de servicios",
  "executionDate": "2025-02-22"
}
```
