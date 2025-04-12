# Crear una nueva transacción
curl -X POST "http://127.0.0.1:8000/transactions/" -H "Content-Type: application/json" -d @- << 'EOF'
{
  "transaction_id": "SW123456789",
  "sender_name": "John Doe",
  "sender_account": "1234567890",
  "receiver_name": "Jane Doe",
  "receiver_account": "0987654321",
  "amount": "1000.00",
  "currency": "USD"
}
EOF

# Obtener todas las transacciones
curl -X GET "http://127.0.0.1:8000/transactions/"

# Obtener una transacción específica
curl -X GET "http://127.0.0.1:8000/transactions/SW123456789/"

# Actualizar una transacción
curl -X PUT "http://127.0.0.1:8000/transactions/SW123456789/" -H "Content-Type: application/json" -d @- << 'EOF'
{
  "status": "COMPLETED"
}
EOF

# Eliminar una transacción
curl -X DELETE "http://127.0.0.1:8000/transactions/SW123456789/"
