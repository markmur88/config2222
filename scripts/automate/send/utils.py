import uuid

def generate_uuid():
    return str(uuid.uuid4())

def generate_end_to_end_identification(paymentId: str):
    return paymentId

def correlation_id(paymentId: str):
    return f"RET{paymentId}"

def check_required_headers(headers):
    required_headers = [
        'idempotency-id', 'processId', 'otp', 'Correlation-Id', 'Origin', 'Accept', 
        'X-Requested-With', 'Content-Type', 'Access-Control-Request-Method', 
        'Access-Control-Request-Headers', 'Authorization', 'Cookie', 
        'X-Frame-Options', 'X-Content-Type-Options', 'Strict-Transport-Security', 
        'previewsignature'
    ]
    for header in required_headers:
        if header not in headers:
            raise ValueError(f"Missing required header: {header}")
