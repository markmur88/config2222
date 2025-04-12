from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/swift/transaction', methods=['POST'])
def swift_transaction():
    data = request.get_json()
    # Validate input data
    if not data or 'account_from' not in data or 'account_to' not in data or 'amount' not in data:
        return jsonify({'error': 'Invalid input'}), 400
    
    account_from = data['account_from']
    account_to = data['account_to']
    amount = data['amount']
    
    # Process the transaction
    # ...existing code...
    
    # Return a success response
    return jsonify({'status': 'success', 'transaction_id': '123456'}), 200

if __name__ == '__main__':
    app.run(debug=True)
